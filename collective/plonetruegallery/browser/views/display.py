from collective.plonetruegallery.interfaces import IDisplayType
from collective.plonetruegallery.interfaces import IFancyBoxDisplaySettings
from collective.plonetruegallery.interfaces import IHighSlideDisplaySettings
from collective.plonetruegallery.interfaces import IBatchingDisplayType
from collective.plonetruegallery.interfaces import IGallerifficDisplaySettings
from plone.memoize.view import memoize
from zope.interface import implements
from collective.plonetruegallery import PTGMessageFactory as _
from collective.plonetruegallery.settings import GallerySettings
from Products.CMFPlone.PloneBatch import Batch
from zope.component import getMultiAdapter
from Products.Five import BrowserView
from collective.plonetruegallery.utils import getGalleryAdapter
from collective.plonetruegallery.utils import createSettingsFactory


def jsbool(val):
    return str(val).lower()


class BaseDisplayType(BrowserView):
    implements(IDisplayType)

    name = None
    description = None
    schema = None
    userWarning = None
    staticFilesRelative = '++resource++plonetruegallery.resources'

    def __init__(self, context, request):
        super(BaseDisplayType, self).__init__(context, request)
        self.adapter = getGalleryAdapter(context, request)
        self.context = self.gallery = self.adapter.gallery
        self.settings = GallerySettings(context,
                            interfaces=[self.adapter.schema, self.schema])
        portal_state = getMultiAdapter((context, request),
                                        name='plone_portal_state')
        self.portal_url = portal_state.portal_url()
        self.staticFiles = "%s/%s" % (self.portal_url,
                                      self.staticFilesRelative)

    def content(self):
        return self.index()

    @property
    def height(self):
        return self.adapter.sizes[self.settings.size]['height']

    @property
    def width(self):
        return self.adapter.sizes[self.settings.size]['width']

    @memoize
    def get_start_image_index(self):
        if 'start_image' in self.request:
            si = self.request.get('start_image', '')
            images = self.adapter.cooked_images
            for index in range(0, len(images)):
                if si == images[index]['title']:
                    return index
        return 0

    start_image_index = property(get_start_image_index)


class BatchingDisplayType(BaseDisplayType):
    implements(IDisplayType)

    @memoize
    def uses_start_image(self):
        """
        disable start image if a batch start is specified.
        """
        return bool('start_image' in self.request) and \
            not bool('b_start' in self.request)

    @memoize
    def get_b_start(self):
        if self.uses_start_image():
            page = self.get_page()
            return page * self.settings.batch_size
        else:
            return int(self.request.get('b_start', 0))

    b_start = property(get_b_start)

    @memoize
    def get_start_image_index(self):
        if self.uses_start_image():
            index = super(BatchingDisplayType, self).get_start_image_index()
            return index - (self.get_page() * self.settings.batch_size)
        else:
            return 0

    start_image_index = property(get_start_image_index)

    @memoize
    def get_page(self):
        index = super(BatchingDisplayType, self).get_start_image_index()
        return index / self.settings.batch_size

    @property
    @memoize
    def start_automatically(self):
        return self.uses_start_image() or \
            self.adapter.number_of_images < self.settings.batch_size

    @property
    @memoize
    def batch(self):
        return Batch(self.adapter.cooked_images, self.settings.batch_size,
                                              int(self.b_start), orphan=1)


class FancyBoxDisplayType(BatchingDisplayType):
    implements(IDisplayType, IBatchingDisplayType)

    name = u"fancybox"
    schema = IFancyBoxDisplaySettings
    description = _(u"label_fancybox_display_type",
        default=u"Fancy Box")

    def __init__(self, context, request):
        super(FancyBoxDisplayType, self).__init__(context, request)
        self.staticFiles += '/jquery.fancybox/fancybox'

    def javascript(self):
        return """
<script type="text/javascript"
    src="%(staticFiles)s/jquery.easing-1.3.pack.js"></script>
<script type="text/javascript"
    src="%(staticFiles)s/jquery.mousewheel-3.0.2.pack.js"></script>
<script type="text/javascript"
    src="%(staticFiles)s/jquery.fancybox-1.3.1.pack.js"></script>
  <script type="text/javascript">
    var auto_start = %(start_automatically)s;
    var start_image_index = %(start_index_index)i;
    (function($){
        $(document).ready(function() {
            $("a.fancyzoom-gallery").fancybox({
                'type': 'image',
                'transitionIn': 'elastic',
                'transitionOut': 'elastic'});
            var images = $('a.fancyzoom-gallery');
            if(images.length <= start_image_index){
                start_image_index = 0;
            }
            if(auto_start){
                $(images[start_image_index]).trigger('click');
            }
        });
    })(jQuery);
    </script>
        """ % {
            'start_automatically': str(self.start_automatically).lower(),
            'start_index_index': self.start_image_index,
            'staticFiles': self.staticFiles
        }

    def css(self):
        return """
<link rel="stylesheet" type="text/css"
    href="%(staticFiles)s/jquery.fancybox-1.3.1.css" media="screen" />
""" % {'staticFiles': self.staticFiles}
FancyBoxSettings = createSettingsFactory(FancyBoxDisplayType.schema)


class HighSlideDisplayType(BatchingDisplayType):
    implements(IDisplayType, IBatchingDisplayType)

    name = u"highslide"
    schema = IHighSlideDisplaySettings
    description = _(u"label_highslide_display_type",
        default=u"Highslide - verify terms of use")
    userWarning = _(u"label_highslide_user_warning",
        default=u"You can only use the Highslide gallery for non-commercial "
                u"use unless you purchase a commercial license. "
                u"Please visit http://highslide.com/ for details."
    )

    def css(self):
        return """
<link rel="stylesheet" type="text/css"
    href="%(portal_url)s/++resource++highslide/highslide.css" />
""" % {'portal_url': self.portal_url}

    def javascript(self):
        outlineType = "hs.outlineType = '%s';" % \
                            self.settings.highslide_outlineType
        wrapperClassName = ''

        if 'drop-shadow' in outlineType:
            wrapperClassName = 'dark borderless floating-caption'
            outlineType = ''
        elif 'glossy-dark' in outlineType:
            wrapperClassName = 'dark'
        if len(wrapperClassName) == 0:
            wrapperClassName = 'null'
        else:
            wrapperClassName = "'%s'" % wrapperClassName

        return """
<script type="text/javascript"
    src="%(portal_url)s/++resource++highslide/highslide-with-gallery.js"></script>

<!--[if lt IE 7]>
<link rel="stylesheet" type="text/css"
  href="%(portal_url)s/++resource++highslide/highslide-ie6.css" />
<![endif]-->

<script type="text/javascript">
hs.graphicsDir = '%(portal_url)s/++resource++highslide/graphics/';
hs.align = 'center';
hs.transitions = ['expand', 'crossfade'];
hs.fadeInOut = true;
hs.dimmingOpacity = 0.8;
%(outlineType)s
hs.wrapperClassName = %(wrapperClassName)s;
hs.captionEval = 'this.thumb.alt';
hs.marginBottom = 105; // make room for the thumbstrip and the controls
hs.numberPosition = 'caption';
hs.autoplay = %(timed)s;
hs.transitionDuration = %(duration)i;
hs.addSlideshow({
    interval: %(delay)i,
    repeat: true,
    useControls: true,
    fixedControls: 'fit',
    overlayOptions: {
        position: 'middle center',
        opacity: .7,
        hideOnMouseOut: true
    },
    thumbstrip: {
        position: 'bottom center',
        mode: 'horizontal',
        relativeTo: 'viewport'
    }
});

var auto_start = %(start_automatically)s;
var start_image_index = %(start_index_index)i;

(function($){
$(document).ready(function() {
    var images = $('a.highslide');
    if(images.length <= start_image_index){
        start_image_index = 0;
    }
    if(auto_start){
        $(images[start_image_index]).trigger('click');
    }
});
})(jQuery);
</script>
        """ % {
            'outlineType': outlineType,
            'wrapperClassName': wrapperClassName,
            'delay': self.settings.delay,
            'timed': jsbool(self.settings.timed),
            'duration': self.settings.duration,
            'start_automatically': jsbool(
                self.start_automatically or self.settings.timed),
            'start_index_index': self.start_image_index,
            'portal_url': self.portal_url
        }
HighSlideSettings = createSettingsFactory(HighSlideDisplayType.schema)


class GallerifficDisplayType(BaseDisplayType):
    implements(IDisplayType)

    name = u"galleriffic"
    schema = IGallerifficDisplaySettings
    description = _(u"label_galleriffic_display_type",
        default=u"Galleriffic")

    def css(self):
        return """
<link rel="stylesheet" type="text/css"
    href="%(staticFiles)s/galleriffic/css/style.css" />

<style>
div.slideshow-container,div.loader,div.slideshow a.advance-link{
    height: %(height)ipx;
    width: %(box_width)ipx;
}
span.image-caption {
    width: %(width)ipx;
}
div.slideshow a.advance-link{
    line-height: %(height)ipx;
}
div.slideshow span.image-wrapper a img{
    max-width: %(width)ipx;
    max-height: %(height)ipx;
}

ul.thumbs li{
    height: %(thumbnail_height)ipx;
}
</style>
""" % {
            'staticFiles': self.staticFiles,
            'height': self.height,
            'width': self.width,
            'box_width': self.width + 10,
            'thumbnail_height': self.adapter.sizes['thumb']['height']
        }

    def javascript(self):
        return """
<script type="text/javascript"
    src="%(portal_url)s/++resource++jquery.galleriffic.js"></script>
<script type="text/javascript"
    src="%(portal_url)s/++resource++jquery.opacityrollover.js"></script>
<script type="text/javascript">
    document.write('<style>.noscript { display: none; }</style>');

(function($){
$(document).ready(function() {

    // Initially set opacity on thumbs and add
    // additional styling for hover effect on thumbs
    var onMouseOutOpacity = 0.67;
    var captionOpacity = 0.7;
    $('#thumbs ul.thumbs li').opacityrollover({
        mouseOutOpacity:   onMouseOutOpacity,
        mouseOverOpacity:  1.0,
        fadeSpeed:         'fast',
        exemptionSelector: '.selected'
    });
    // Initialize Advanced Galleriffic Gallery
    var gallery = $('#thumbs').galleriffic({
        delay:                     %(delay)i,
        numThumbs:                 %(batch_size)i,
        preloadAhead:              10,
        enableTopPager:            true,
        enableBottomPager:         true,
        maxPagesToShow:            7,
        imageContainerSel:         '#slideshow',
        controlsContainerSel:      '#controls',
        captionContainerSel:       '#caption',
        loadingContainerSel:       '#loading',
        renderSSControls:          true,
        renderNavControls:         true,
        playLinkText:              'Play Slideshow',
        pauseLinkText:             'Pause Slideshow',
        prevLinkText:              '&lsaquo; Previous Photo',
        nextLinkText:              'Next Photo &rsaquo;',
        nextPageLinkText:          'Next &rsaquo;',
        prevPageLinkText:          '&lsaquo; Prev',
        enableHistory:             true,
        autoStart:                 %(timed)s,
        syncTransitions:           true,
        defaultTransitionDuration: %(duration)i,
        onSlideChange:             function(prevIndex, nextIndex) {
            this.find('ul.thumbs').children()
                .eq(prevIndex).fadeTo('fast', onMouseOutOpacity).end()
                .eq(nextIndex).fadeTo('fast', 1.0);
        },
        onTransitionOut:           function(slide, caption, isSync, callback) {
            slide.fadeTo(this.getDefaultTransitionDuration(isSync), 0.0, callback);
            caption.fadeTo(this.getDefaultTransitionDuration(isSync), 0.0);
        },
        onTransitionIn:            function(slide, caption, isSync) {
            var duration = this.getDefaultTransitionDuration(isSync);
            slide.fadeTo(duration, 1.0);
            var slideImage = slide.find('img');
            caption.width(slideImage.width())
                .css({
                    'bottom' : Math.floor((slide.height() - slideImage.outerHeight()) / 2),
                    'left' : Math.floor((slide.width() - slideImage.width()) / 2) + slideImage.outerWidth() - slideImage.width()
                })
                .fadeTo(duration, captionOpacity);
        },
        onPageTransitionOut:       function(callback) {
            this.fadeTo('fast', 0.0, callback);
        },
        onPageTransitionIn:        function() {
            this.fadeTo('fast', 1.0);
        },
        onImageAdded:              function(imageData, $li) {
            $li.opacityrollover({
                mouseOutOpacity:   onMouseOutOpacity,
                mouseOverOpacity:  1.0,
                fadeSpeed:         'fast',
                exemptionSelector: '.selected'
            });
        }
    });
});
})(jQuery);

</script>
""" % {
    'portal_url': self.portal_url,
    'timed': jsbool(self.settings.timed),
    'delay': self.settings.delay,
    'duration': self.settings.duration,
    'batch_size': self.settings.batch_size
}
GallerifficSettings = createSettingsFactory(GallerifficDisplayType.schema)
