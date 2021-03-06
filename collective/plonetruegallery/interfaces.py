from zope.interface import Interface, Attribute
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from collective.plonetruegallery import PTGMessageFactory as _


class IGalleryAdapter(Interface):
    sizes = Attribute("image size mappings for the gallery type")
    schema = Attribute("Schema of gallery specific")
    name = Attribute("Name of the gallery")
    description = Attribute("Description of gallery type")
    cook_delay = Attribute("Time between updates of gallery images.  "
        "This update of images can be forced by appending refresh on "
        "a gallery.")
    cooked_images = Attribute("The images after they've been cooked up.")

    def cook():
        """
        this will make it so the gallery's images are not aggregated every
        single time the gallery is displayed.
        """

    def time_to_cook():
        """
        called to see if it is time to the cook the gallery.
        """

    def get_random_image():
        """
        returns a random image with data.
        returns an empty dict if the gallery is empty.
        """

    def log_error():
        """
        provides an easy way to log errors in gallery adapters.
        we don't want an adapter to prevent a page from loading...
        Who knows what kind of odd behavior some adapters may run into
        when working with picasa or flickr apis...
        """

    def retrieve_images():
        """
        This method retrieves all the images to be cooked
        """
    def number_of_images():
        """"""

    def get_all_images():
        """
        returns all the cooked images for the gallery
        """


class IBasicAdapter(IGalleryAdapter):
    """
    Use plone to manage images for the gallery.
    """

    size_map = Attribute("allows us to map specific sizes to plone urls")


class IFlickrAdapter(IGalleryAdapter):
    """
    """

    flickr = Attribute("returns a flickrapi object for the api key")

    def get_flickr_user_id(username):
        """
        Returns the actual user id of someone given a username.
        if a username is not given, it will use the one in its
        settings
        """

    def get_flickr_photoset_id(theset=None, userid=None):
        """
        Returns the photoset id given a set name and user id.
        Uses the set and get_flickr_user_id() if they are
        not specified.
        """

    def get_mini_photo_url(photo):
        """
        takes a photo and creates the thumbnail photo url
        """

    def get_photo_link(photo):
        """
        creates the photo link url
        """

    def get_large_photo_url(photo):
        """
        create the large photo url
        """


class IPicasaAdapter(IGalleryAdapter):
    """
    """

    gd_client = Attribute("property for gd_client instance")

    def get_album_name(name, user):
        """
        Returns the selected album name and user.
        Uses name and user in settings if not specified.
        """

    def feed():
        """
        Returns the picasa feed for the given album.
        """


class IDisplayType(Interface):
    name = Attribute("name of display type")
    description = Attribute("description of type")
    schema = Attribute("Options for this display type")
    userWarning = Attribute("A warning to be displayed to to "
                            "the user if they use this type.")
    width = Attribute("The width of the gallery")
    height = Attribute("The height of the gallery")
    start_image_index = Attribute("What image the gallery should "
                                  "start playing at.")

    def content():
        """
        the content of the display yet
        """

    def javascript():
        """
        content to be included in javascript area of template
        """

    def css():
        """
        content to be included in css area of template
        """


class IBatchingDisplayType(Interface):

    def uses_start_image(self):
        """
        disable start image if a batch start is specified.
        """

    b_start = Attribute("")
    start_image_index = Attribute("")

    def get_page(self):
        """"""

    start_automatically = Attribute("")
    batch = Attribute("")


class IGallery(Interface):
    """
    marker interface for content types that implement
    the gallery
    """


class IGallerySettings(Interface):

    gallery_type = schema.Choice(
        title=_(u"label_gallery_type", default=u"Type"),
        description=_(u"description_gallery_type",
            default=u"Select the type of gallery you want this to be.  "
                    u"If you select something other than default, you "
                    u"must fill out the information in the corresponding "
                    u"tab for that gallery type."),
        vocabulary="collective.plonetruegallery.GalleryTypeVocabulary",
        default="basic"
    )

    # the specific options for the gallery types will be added
    # dynamcially in the form
    size = schema.Choice(
        title=_(u"label_gallery_size", default=u"Size"),
        description=_(u"description_gallery_size",
            default=u"The actual sizes used can vary depending on the "
                    u"gallery type that is used since different services "
                    u"have different size constraints."),
        default='medium',
        vocabulary=SimpleVocabulary([
            SimpleTerm('small', 'small', _(u"label_size_small",
                                            default=u'Small')),
            SimpleTerm('medium', 'medium', _(u"label_size_medium",
                                            default=u'Medium')),
            SimpleTerm('large', 'large', _(u"label_size_large",
                                            default=u'Large'))
        ])
    )

    thumb_size = schema.Choice(
        title=_(u"label_thumb_size", default=u"Thumbnail image size"),
        description=_(u"description_thumb_size",
            default=u"The size of thumbnail images. "
                    u"(*Fancybox* display type)"
        ),
        default='thumb',
        vocabulary=SimpleVocabulary([
            SimpleTerm('tile', 'tile', _(u"label_tile", default=u"tile")),
            SimpleTerm('thumb', 'thumb', _(u"label_thumb", default=u"thumb")),
            SimpleTerm('mini', 'mini', _(u"label_mini", default=u"mini")),
            SimpleTerm('preview', 'preview', _(u"label_preview",
                                                default=u"preview")),
        ])
    )

    display_type = schema.Choice(
        title=_(u"label_gallery_display_type",
                default=u"Gallery Display Type"),
        description=_(
            u"label_gallery_display_type_description",
            default=u"Choose the method in which the "
                    u"gallery should be displayed"
        ),
        default="galleriffic",
        vocabulary="collective.plonetruegallery.DisplayTypes"
    )

    # the options for the display type will also be added dynamically
    timed = schema.Bool(
        title=_(u"label_timed", default=u"Timed?"),
        description=_(u"description_timed",
            default=u"Should this gallery automatically "
                    u"change images for the user?"
        ),
        default=True
    )

    delay = schema.Int(
        title=_(u"label_delay", default=u"Delay"),
        description=_(u"description_delay",
            default=u"If slide show is timed, the delay sets "
                    u"how long before the next image is shown in miliseconds."
        ),
        default=5000,
        required=True
    )

    duration = schema.Int(
        title=_(u"label_image_change_duration", default=u"Change Duration"),
        description=_(u"description_fade_in_duration",
            default=u"The amount of time the change effect should "
                    u"take in miliseconds."
        ),
        default=500,
        required=True
    )

    show_subgalleries = schema.Bool(
        title=_(u"label_show_subgalleries", default=u"Show Sub-Galleries?"),
        description=_(u"description_show_subgalleries",
            default=u"If you select this option, previews for all "
                    u"nested galleries will show up below this gallery."
        ),
        default=True
    )

    batch_size = schema.Int(
        title=_(u"label_batch_size", default=u"Batch Size"),
        description=_(u"description_batch_size",
            default=u"The amount of images shown in one page. "
                    u"This is not used for all display types."
        ),
        default=50,
        required=True
    )


class IBaseSettings(Interface):
    pass


class IFancyBoxDisplaySettings(IBaseSettings):
    pass


class IHighSlideDisplaySettings(IBaseSettings):

    highslide_outlineType = schema.Choice(
        title=_(u"label_highslide_outlineType", default=u"Image outline type"),
        description=_(u"description_highslide_outlineType",
            default=u"The style of the border around the image. "
        ),
        default='drop-shadow',
        vocabulary=SimpleVocabulary([
            SimpleTerm('rounded-white', 'rounded-white',
                _(u"label_highslide_outlineType_rounded_white",
                                    default=u"Rounded White")),
            SimpleTerm('outer-glow', 'outer-glow',
                _(u"label_highslide_outlineType_outer_glow",
                                    default=u"Outer Glow")),
            SimpleTerm('drop-shadow', 'drop-shadow',
                _(u"label_highslide_outlineType_drop_shadow",
                                    default=u"Drop Shadow")),
            SimpleTerm('glossy-dark', 'glossy-dark',
                _(u"label_highslide_outlineType_glossy_dark",
                                    default=u"Glossy Dark")
            )
        ])
    )


class IGallerifficDisplaySettings(IBaseSettings):

    gallerific_style = schema.Choice(
        title=_(u"label_gallerific-style", default=u"Layout"),
        description=_(u"description_gallerific-style",
            default=u"The style of the Galleriffic layout. "
        ),
        default='style.css',
        vocabulary=SimpleVocabulary([
            SimpleTerm('style.css', 'style.css',
                _(u"label_gallerific_style",
                                    default=u"Default Layout")),
            SimpleTerm('style2.css', 'style2.css',
                _(u"label_gallerific_style2",
                                    default=u"Linklayout")
            )
        ])
    )


class IS3sliderDisplaySettings(IBaseSettings):
    pass


class IPikachooseDisplaySettings(IBaseSettings):
    pikachoose_showtooltips = schema.Bool(
        title=_(u"label_pikachoose_tooltip", default=u"Show tooltip"),
        default=False
    )

    pikachoose_showcarousel = schema.Bool(
        title=_(u"label_pikachoose_carousel", default=u"Hide carousel"),
        default=False
    )

    pikachoose_showcaption = schema.Bool(
        title=_(u"label_pikachoose_caption", default=u"Show caption"),
        default=True
    )

    pikachoose_vertical = schema.Bool(
        title=_(u"label_pikachoose_vertical", default=u"Vertical"),
        default=False
    )

    pikachoose_transition = schema.Choice(
        title=_(u"label_pikachoose_transition", default=u"Transition"),
        default=4,
        vocabulary=SimpleVocabulary([
            SimpleTerm(1, 1,
                _(u"label_transitions", default=u"Full frame cross fade")),
            SimpleTerm(2, 2,
                _(u"label_transitions2", default=u"Paneled fold out")),
            SimpleTerm(3, 3,
                _(u"label_transitions3", default=u"Horizontal blinds")),
            SimpleTerm(4, 4,
                _(u"label_transitions4", default=u"Vertical blinds")),
            SimpleTerm(5, 5,
                _(u"label_transitions5", default=u"Small box random fades")),
            SimpleTerm(6, 6,
                _(u"label_transitions6", default=u"Full image blind slide")),
            SimpleTerm(0, 0,
                _(u"label_transitions7", default=u"Fade out then fade in")
            )
        ])
    )


class IGalleriaDisplaySettings(IBaseSettings):
    galleria_theme = schema.Choice(
        title=_(u"galleria_theme_title", default=u"Theme"),
        default='dark',
        vocabulary=SimpleVocabulary([
            SimpleTerm('dark', 'dark', _(u"label_dark", default=u"Dark")),
            SimpleTerm('light', 'light', _(u"label_light", default=u"Light")),
            SimpleTerm('classic', 'classic', _(u"label_classic",
                                               default=u"Classic"))
        ])
    )

    galleria_transition = schema.Choice(
        title=_(u"galleria_transition", default=u"Transition"),
        default='fadeslide',
        vocabulary=SimpleVocabulary([
            SimpleTerm('fadeslide', 'fadeslide', _(u"label_fadeslide",
                default=u"Fade Slide - fade between images and "
                        u"slide slightly at the same time")),
            SimpleTerm('fade', 'fade', _(u"label_fade",
                default=u"Fade - crossfade betweens images")),
            SimpleTerm('flash', 'flash', _(u"label_flash",
                default=u"Flash - fades into background color "
                        u"between images")),
            SimpleTerm('pulse', 'pulse', _(u"label_pulse",
                default=u"Pulse - quickly removes the image into background "
                        u"color, then fades the next image")),
            SimpleTerm('slide', 'slide', _(u"label_slide",
                default=u"Slide - slides the images depending on image "
                        u"position"))
        ])
    )


class IBasicGallerySettings(IBaseSettings):
    pass


class IFlickrGallerySettings(IBaseSettings):

    flickr_username = schema.TextLine(
        title=_(u"label_flickr_username", default=u"flickr username"),
        description=_(u"description_flickr_username",
            default=u"The username/id of your flickr account. "
                    u"(*flickr* gallery type)"
        ),
        required=False
    )

    flickr_set = schema.TextLine(
        title=_(u"label_flickr_set", default="Flickr Set"),
        description=_(u"description_flickr_set",
            default=u"Name/id of your flickr set."
                    u"(*flickr* gallery type)"
        ),
        required=False
    )


class IPicasaGallerySettings(IBaseSettings):

    picasa_username = schema.TextLine(
        title=_(u"label_picasa_username", default=u"GMail address"),
        description=_(u"description_picasa_username",
            default=u"GMail address of who this album belongs to. "
                    u"(*Picasa* gallery type)"
        ),
        required=False
    )

    picasa_album = schema.TextLine(
        title=_(u"label_picasa_album", default=u"Picasa Album"),
        description=_(u"description_picasa_album",
            default=u"Name of your picasa web album. "
                    u"This will be the qualified name you'll see in "
                    u"the address bar or the full length name of the "
                    u"album. (*Picasa* gallery type)"
        ),
        required=False
    )


class IImageInformationRetriever(Interface):
    """
    This interface is interesting for everybody who wants to filter
    the items to be shown in a gallery view
    """
    def getImageInformation(self, size):
        """
        Return a list of Information relevant for gallery display for each
        image.
        Size should be a hint of the image size to use, in string format.
        The standard implementations support the following sizes, which
        map to the given size of the archetypes Image size:

            small -> mini
            medium -> preview
            large -> large

        This information returned consists of:
        image_url
            The URL to the image itself
        thumb_url
            The URL to a thumbnail version of the image
        link
            The Link to which an image must point to
        title
            The image title
        description
            The image description
        """
