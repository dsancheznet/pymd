## 11 APR 2020
* Initial commit
* Reload funcionality

## 16 APR 2020
* Reload style if a new stylesheet is selected
* Select last used stylesheet as default

## 18 APR 2020
* Established CTRL+R shortcut for reloading the file

## 19 APR 2020
* Changed from WebKit1 to WebKit2 since WebKit1 did not support printing
* Added a print button to the UI
* Added a keyboard shortcut to print
* Implemented a print method to print the webview's content
* Added an information dialog to inform the user that the data has been sent to the printer
* As we have new functions available, I decided to go a minor version up to v1.1 and released the application out of beta.
* Implemented the possibility to load data from Files or from parameters
* Implemented error checking on the existence of a file
* Edited .desktop file to include the MimeType and %F option, see https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s06.html

## 20 APR 2020
* The popup will now close as soon as a different stylesheet is selected
* Mistune library has been updated, so I've updated the minimum requirements as well.
* The Mistune update brings support of checkboxes
* Added \*.mkd as admissible extension
* Included a proposed .desktop file
* Included the neccessary configuration files
* Added an about box (F1)
