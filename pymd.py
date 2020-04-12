#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# pymd, a markdown viewer for Linux by D.Sánchez
# This program is published under the EU-GPL, get your copy at
# https://joinup.ec.europa.eu/sites/default/files/custom-page/attachment/eupl_v1.2_en.pdf
# Based on the GTK3 Library in pyGObject for python and driven by the mistune library by
# Hsiaoming Yang, published at https://github.com/lepture/mistune
# You may have to install the dependencies from github. Please read the README file.

import gi, os, glob, configobj, mistune
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import Gtk, Gdk, WebKit, Gio, GObject
from mistune.directives import DirectiveToc
from mistune.directives import Admonition

#Define a version number to be able to change it just in one place
global VERSION_NUMBER, WEB_PAGE
VERSION_NUMBER = "1.0b"
WEB_PAGE="https://github.com/dsancheznet/pymd/"


class ImagePathRenderer(mistune.HTMLRenderer):
    """
        Class to override the image tag of mistune's HTMLRenderer
        This code is mostly identical to the original code, with the exception
        of the basepath.
    """

    def __init__(self, tmpPath ):
        #Init superclass
        mistune.HTMLRenderer.__init__( self )
        #Establish basepath
        self.BASEPATH = tmpPath

    def image(self, src, alt="", title=None):
        #Is the image a remote image?
        if ("http://" in src) or ("https://" in src):
            #YES - Then do not append the local basepath
            s = '<img src="' + src + '" alt="' + alt + '"'
        else:
            #NO - Insert local basepath before filename
            s = '<img src="' + "file://" + self.BASEPATH + src + '" alt="' + alt + '"'
        #Do we have a title?
        if title:
            #Append escaped title to our img
            s += ' title="' + escape_html(title) + '"'
        #Return data with the closing tag
        return s + ' />'


class MainWindow(Gtk.Window):
    """
        This class defines the main window of the application
    """

    def __init__(self):
        #Instantiate config file parser
        self.cConfig = configobj.ConfigObj( os.path.expanduser("~")+'/.config/pymd/default.config') #TODO: Error checking
        #Define a path, where the css files a loaded from
        self.myCSSPath = os.path.expanduser("~")+'/.config/pymd/css/' #TODO: Error checking
        #Create a list holding all css files in that directory (list comprehention)
        tmpCSSFiles = [os.path.basename(tmp) for tmp in glob.glob( self.myCSSPath + "*.css")]
        #-----------------------------------------------------------Construct UI
        #Configure Main Window
        Gtk.Window.__init__(self, title="pymd")
        self.set_border_width( 5 )
        self.set_default_size( int(self.cConfig['Width']), int(self.cConfig['Height']) ) # I might delete this in the future since for this application I prefer a fixed size.
        self.set_position( Gtk.WindowPosition.CENTER )
        #---------- Header Bar

        #Configure a Headerbar
        self.cHeaderBar = Gtk.HeaderBar()
        self.cHeaderBar.set_show_close_button(True)
        self.cHeaderBar.props.title = "pymd " + VERSION_NUMBER
        self.cHeaderBar.props.subtitle = ""
        self.set_titlebar(self.cHeaderBar)

        #Buttons for Headerbar
        myConfigButton = Gtk.Button()
        myConfigButton.props.relief = Gtk.ReliefStyle.NONE
        myConfigButton.add( Gtk.Image.new_from_gicon( Gio.ThemedIcon( name="emblem-system-symbolic" ), Gtk.IconSize.BUTTON ) )
        myConfigButton.connect( "clicked", self.onConfigButtonClicked )

        myOpenButton = Gtk.Button()
        myOpenButton.props.relief = Gtk.ReliefStyle.NONE
        myOpenButton.add( Gtk.Image.new_from_gicon( Gio.ThemedIcon( name="folder-open" ), Gtk.IconSize.BUTTON ) )
        myOpenButton.connect( "clicked", self.onOpenButtonClicked )

        myUpdateButton = Gtk.Button()
        myUpdateButton.props.relief = Gtk.ReliefStyle.NONE
        myUpdateButton.add( Gtk.Image.new_from_gicon( Gio.ThemedIcon( name="emblem-synchronizing-symbolic" ), Gtk.IconSize.BUTTON ) )
        myUpdateButton.connect( "clicked", self.onUpdateBuffonClicked )

        #Pack everything
        self.cHeaderBar.pack_start( myConfigButton )
        self.cHeaderBar.pack_end( myOpenButton )
        self.cHeaderBar.pack_end( myUpdateButton )
        #----------Header Bar ***END***

        #----------Scroller
        #Create a scrollable container for the TextView
        self.myScroller = Gtk.ScrolledWindow()
        self.myScroller.set_border_width( 2 )
        self.myScroller.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )

        #Create a webview
        self.myWebView = WebKit.WebView()
        self.myWebView.get_settings().allow_universal_access_from_file_urls = True;
        self.myWebView.load_string( '<html><body><br><center>Empty...</center></body></html>', "text/html", "UTF-8", "file://" )
        self.myWebView.props.settings.props.enable_default_context_menu = False
        self.myScroller.add( self.myWebView )
        self.add( self.myScroller )
        #----------Scroller ***END***

        #---------- Popover
        #Define popover items
        self.myCSSFile = Gtk.ComboBoxText()
        for tmpItem in tmpCSSFiles:
            self.myCSSFile.append_text( tmpItem )
        self.myCSSFile.set_active(0)
        #Define popover and it's properties
        self.cPopover = Gtk.Popover()
        self.cPopover.set_border_width( 10 )
        #Pack popover
        tmpVerticalBox = Gtk.Box( orientation= Gtk.Orientation.VERTICAL )
        tmpHorizontalBox = Gtk.Box( orientation= Gtk.Orientation.HORIZONTAL)
        tmpHorizontalBox.pack_start( Gtk.Label("Stylesheet"), False, False, 2)
        tmpVerticalBox.pack_start(tmpHorizontalBox, True, False, 2)
        tmpVerticalBox.pack_start( self.myCSSFile, True, False, 10 )
        self.cPopover.add( tmpVerticalBox )
        #Connect popover
        self.cPopover.set_position(Gtk.PositionType.BOTTOM)
        #---------- Popover ***END***
        #Save Window data before closing
        self.connect( "delete-event", self.mainWindowDelete )
        #Connect the destroy signal to the main loop quit function
        self.connect("destroy", Gtk.main_quit )

    def mainWindowDelete( self, widget, data=None ):
        pass

    def onConfigButtonClicked( self, widget ):
        #Position the popover
        self.cPopover.set_relative_to( widget )
        #Show it...
        self.cPopover.show_all()
        #Do your thing
        self.cPopover.popup()

    def loadFileData( self, tmpFilename ):
        #DEBUG: print('Reloading...')
        #Create a mistune instance with all plugins enabled and a custom renderer
        tmpMarkdown = mistune.create_markdown( escape=False, renderer=ImagePathRenderer( os.path.dirname( tmpFilename )+ "/"  ), plugins=[Admonition(), DirectiveToc(), 'url', 'strikethrough', 'footnotes', 'table'],)
        #Open the file for reading // TODO: Error checking -> Filie must be readable
        tmpMarkDownFile = open( tmpFilename, "r" )
        #Load the contents of the file as raw data
        tmpRawMarkdown = tmpMarkDownFile.read()
        #Define a string to prepend
        tmpPreHTML = '<html><head><link rel="stylesheet" type="text/css" href="file://' + self.myCSSPath + self.myCSSFile.get_active_text() + '"></head><body class="markdown-body">'
        #Define a string to append
        tmpPostHTML = "</body></html>"
        #Define a base uri // HINT: Without this, we are getting errors trying to load local files
        tmpBaseURI = "file://"
        #Load the data into the webview.
        self.myWebView.load_string( tmpPreHTML + tmpMarkdown( tmpRawMarkdown ) + tmpPostHTML, "text/html", "UTF-8", tmpBaseURI  )
        #Close the file we opened for reading
        tmpMarkDownFile.close()
        #DEBUG: print(tmpPreHTML + tmpMarkdown( tmpRawMarkdown ) + tmpPostHTML)

    def onUpdateBuffonClicked( self, widget ):
        #Call the loader with the filename as parameter
        self.loadFileData( self.cHeaderBar.props.subtitle )

    def onOpenButtonClicked( self, widget ):
        #Open a dialog to choose a file
        tmpDialog = Gtk.FileChooserDialog(
                "Please choose a markdown file",
                self,
                Gtk.FileChooserAction.OPEN ,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK))
        #DEBUG: tmpDialog.set_default_size(500, 350)
        #Create a filter (we only want to permit supported files)
        tmpFilter = Gtk.FileFilter()
        #Give it a name
        tmpFilter.set_name( "Markdown Files" )
        #Option1
        tmpFilter.add_pattern( "*.md" )
        #Option2
        tmpFilter.add_pattern( "*.markdown" )
        #Add the filter to the dialog
        tmpDialog.add_filter( tmpFilter )
        #Run the dialog (i.e. show it)
        tmpResponse = tmpDialog.run()
        #Did the user confirm the selection with OK?
        if tmpResponse == Gtk.ResponseType.OK:
            #YES - Put the file name on the headerbar
            self.cHeaderBar.props.subtitle = tmpDialog.get_filename()
            #Load the data into the webview
            self.loadFileData( tmpDialog.get_filename() )
        elif tmpResponse == Gtk.ResponseType.CANCEL:
            #NO - Cancel was pressed
            #Let's do nothing, until I think about something to do here.
            pass
        #Destroy de dialog
        tmpDialog.destroy()


#Create Main Window
myWindow = MainWindow()

#Connect the destroy signal to the main loop quit function
myWindow.connect("destroy", Gtk.main_quit)

#Show Windows on screen
myWindow.show_all()

#Main Loop
Gtk.main()
