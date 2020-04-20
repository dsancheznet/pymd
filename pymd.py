#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# pymd, a markdown viewer for Linux by D.Sánchez
# This program is published under the EU-GPL, get your copy at
# https://joinup.ec.europa.eu/sites/default/files/custom-page/attachment/eupl_v1.2_en.pdf
# Based on the GTK3 Library in pyGObject for python and driven by the mistune library by
# Hsiaoming Yang, published at https://github.com/lepture/mistune
# You may have to install the dependencies from github. Please read the README file.

import sys, os, gi, glob, configobj, mistune
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, Gdk, WebKit2, Gio, GObject, Keybinder
from mistune.directives import DirectiveToc
from mistune.directives import Admonition

#Define a version number to be able to change it just in one place
global VERSION_NUMBER, WEB_PAGE
VERSION_NUMBER = "1.1"
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

    def __init__( self, tmpDefaultFile="" ):
        #Instantiate config file parser
        self.cConfig = configobj.ConfigObj( os.path.expanduser("~")+'/.config/pymd/default.config')
        Keybinder.init()
        Keybinder.bind("<Ctrl>R", self.onUpdateButtonClicked )
        Keybinder.bind("<Ctrl>P", self.onPrintButtonClicked )
        Keybinder.bind("F1", self.onAboutOpen )
        #TODO: Error checking
        #Define a path, where the css files a loaded from
        self.myCSSPath = os.path.expanduser("~")+'/.config/pymd/css/' #TODO: Error checking
        #Create a list holding all css files in that directory (list comprehention)
        tmpCSSFiles = [os.path.basename(tmp) for tmp in glob.glob( self.myCSSPath + "*.css")]
        #-----------------------------------------------------------Construct UI
        #Configure Main Window
        Gtk.Window.__init__(self, title="pymd")
        self.set_border_width( 5 )
        if self.cConfig['Save_Geometry'] == 1:
            self.set_default_size( int(self.cConfig['Width']), int(self.cConfig['Height']) )
        else:
            self.set_default_size( 750,600 )
            self.set_position( Gtk.WindowPosition.CENTER )
        #---------- Header Bar

        #Configure a Headerbar
        self.cHeaderBar = Gtk.HeaderBar()
        self.cHeaderBar.set_show_close_button(True)
        self.cHeaderBar.props.title = "pymd " + VERSION_NUMBER
        self.cHeaderBar.props.subtitle = tmpDefaultFile
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
        myUpdateButton.connect( "clicked", self.onUpdateButtonClicked )

        myPrintButton = Gtk.Button()
        myPrintButton.props.relief = Gtk.ReliefStyle.NONE
        myPrintButton.add( Gtk.Image.new_from_gicon( Gio.ThemedIcon( name="printer-printing" ), Gtk.IconSize.BUTTON ) )
        myPrintButton.connect( "clicked", self.onPrintButtonClicked )

        #Pack everything
        self.cHeaderBar.pack_start( myConfigButton )
        self.cHeaderBar.pack_end( myOpenButton )
        self.cHeaderBar.pack_end( myUpdateButton )
        self.cHeaderBar.pack_start( myPrintButton )
        #----------Header Bar ***END***

        #----------Scroller
        #Create a scrollable container for the TextView
        self.myScroller = Gtk.ScrolledWindow()
        self.myScroller.set_border_width( 2 )
        self.myScroller.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )

        #Create a webview
        self.myWebView = WebKit2.WebView()
        self.myWebView.get_settings().allow_universal_access_from_file_urls = True;
        self.myWebView.connect('context-menu', self.contextMenuCallback )
        self.myWebView.load_html('<html><body><br><center>Empty...</center></body></html>', "file://" )
        #self.myWebView.props.settings.props.enable_default_context_menu = False
        self.myScroller.add( self.myWebView )
        self.add( self.myScroller )
        #----------Scroller ***END***

        #---------- Popover
        #Define popover items
        self.myCSSFile = Gtk.ComboBoxText()
        for tmpItem in tmpCSSFiles:
            if tmpItem == self.cConfig['CSS']:
                self.myCSSFile.prepend_text( tmpItem )
            else:
                self.myCSSFile.append_text( tmpItem )
        self.myCSSFile.set_active(0)
        self.myCSSFile.connect( "changed", self.onComboPopdown )
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
        self.cPopover.connect( "closed", self.onPopoverClosed )
        self.cPopover.set_position(Gtk.PositionType.BOTTOM)
        #---------- Popover ***END***
        #Save Window data before closing
        self.connect( "delete-event", self.mainWindowDelete )
        #Connect the destroy signal to the main loop quit function
        self.connect("destroy", Gtk.main_quit )
        #Load the data (it won't do anythign if subtitle is empty)
        self.loadFileData( self.cHeaderBar.props.subtitle )

    def contextMenuCallback( self, web_view, context_menu, event, hit_test_result ):
        #This callback is to avoid opening a context menu
        return True

    def mainWindowDelete( self, widget, data=None ):
        #Save default styelsheet
        self.cConfig['CSS'] = self.myCSSFile.get_active_text()
        self.cConfig.write()

    def onPopoverClosed( self, widget ):
        #This doesn't do anything anymore, but I'll leave it in
        #for future functions that are already planned
        pass

    def onConfigButtonClicked( self, widget ):
        #Position the popover
        self.cPopover.set_relative_to( widget )
        #Show it...
        self.cPopover.show_all()
        #Do your thing
        self.cPopover.popup()

    def onUpdateButtonClicked( self, widget ):
        #Do we have a file loaded?
        if self.cHeaderBar.props.subtitle != "":
            #YES - Call the loader with the filename as parameter
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
        tmpFilter.add_pattern( "*.mkd" )
        #Option3
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

    def onPrintButtonClicked( self, widget ):
        #Do we have a file open?
        if self.cHeaderBar.props.subtitle != "":
            #YES - Launch print dialog
            tmpOperation = WebKit2.PrintOperation.new( self.myWebView )
            if tmpOperation.run_dialog() == WebKit2.PrintOperationResponse.CANCEL:
                print("Print Cancelled!")
            else:
                tmpDialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Print Job")
                tmpDialog.format_secondary_text( "Your print job has been sent to the printer...")
                tmpDialog.run()
                tmpDialog.destroy()

    def onComboPopdown( self, widget ):
        #Is there any file open?
        if self.cHeaderBar.props.subtitle != "":
            #YES - Reload current file
            self.loadFileData( self.cHeaderBar.props.subtitle )
        #Close the popup
        self.cPopover.popdown()

    def onAboutOpen( self, widget ):
        tmpAuthor = ["D.Sánchez @DSanchezNET"]
        tmpBox = Gtk.AboutDialog(parent=self,transient_for=self, modal=True)
        tmpBox.set_program_name("pymd")
        tmpBox.set_version( VERSION_NUMBER )
        tmpBox.set_comments("A markdown viewer with extended syntax")
        tmpBox.set_copyright("Copyright © 2020 D.Sánchez")
        tmpBox.set_website( WEB_PAGE )
        tmpBox.set_authors( tmpAuthor )
        tmpBox.set_license_type( Gtk.License.GPL_3_0 )
        tmpBox.set_logo_icon_name( "package_wordprocessing" )
        tmpBox.add_credit_section( "Projects that made pymd possible:",
            ["Mistune by Hsiaoming Yang", "https://github.com/lepture/mistune", "markdowncss by John Otander", "http://markdowncss.github.io/", "markdown-css-themes by Jason Milkins", "http://jasonm23.github.io/markdown-css-themes/", "Github Markdown-CSS by Sindre Sorhus", "https://sindresorhus.com/github-markdown-css/"]
        )
        tmpBox.run()
        tmpBox.destroy()

    def loadFileData( self, tmpFilename ):
        #Does the file we are trying to load exist and is actually a file?
        if os.path.exists( tmpFilename ) and os.path.isfile( tmpFilename ):
            #YES - Create a mistune instance with all plugins enabled and a custom renderer
            tmpMarkdown = mistune.create_markdown( escape=False, renderer=ImagePathRenderer( os.path.dirname( tmpFilename )+ "/"  ), plugins=[Admonition(), DirectiveToc(), 'url', 'strikethrough', 'footnotes', 'table', 'task_lists'],)
            #Open the file for reading // TODO: Error checking -> File must be readable
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
            self.myWebView.load_html( tmpPreHTML + tmpMarkdown( tmpRawMarkdown ) + tmpPostHTML, tmpBaseURI  )
            #Close the file we opened for reading
            tmpMarkDownFile.close()
            #DEBUG: print(tmpPreHTML + tmpMarkdown( tmpRawMarkdown ) + tmpPostHTML)
        else:
            print("File not found...") #TODO: Load an adecuate HTML into the view.

if __name__ == "__main__":

    #Check for parameters
    if len( sys.argv )>1:
        #DEBUG: print( "Arguments: " + str(sys.argv) )
        #Create Main Window with parameter
        myWindow = MainWindow( sys.argv[1] )
    else:
        #Create Main Window without parameter
        myWindow = MainWindow()

    #Connect the destroy signal to the main loop quit function
    myWindow.connect("destroy", Gtk.main_quit)

    #Show Windows on screen
    myWindow.show_all()

    #Main Loop
    Gtk.main()
