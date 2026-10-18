-- Import the reviewed editable deck, preserve notes, and save native Keynote.
-- Usage: osascript presentation/convert_methodology_sample.applescript /absolute/path/to/methodology_sample
on run argv
    set outputFolder to item 1 of argv
    set inputPath to outputFolder & "/NAMA_Methodology_Sample.pptx"
    set keyPath to outputFolder & "/NAMA_Methodology_Sample.key"
    set pdfPath to outputFolder & "/NAMA_Methodology_Keynote_Export.pdf"
    set notesPath to outputFolder & "/NAMA_Methodology_With_Notes.pdf"
    set roundtripPath to outputFolder & "/NAMA_Methodology_Keynote_Export.pptx"
    with timeout of 60 seconds
        tell application id "com.apple.Keynote"
            log "Opening reviewed PPTX in Keynote"
            open (POSIX file inputPath)
            set sampleDeck to missing value
            repeat with attemptIndex from 1 to 25
                repeat with candidateDeck in documents
                    if name of candidateDeck contains "NAMA_Methodology_Sample" then
                        set sampleDeck to candidateDeck
                        exit repeat
                    end if
                end repeat
                if sampleDeck is not missing value then exit repeat
                delay 1
            end repeat
            if sampleDeck is missing value then error "Keynote did not expose the imported document. A welcome, account or import dialog may need attention."
            log "Imported document found"
            tell sampleDeck
                if (count of slides) is not 9 then error "Expected nine slides in the reviewed deck."
                repeat with slideIndex from 1 to 9
                    set indexText to text -2 thru -1 of ("0" & slideIndex)
                    set noteFile to POSIX file (outputFolder & "/notes/slide_" & indexText & ".txt")
                    set noteText to read noteFile as «class utf8»
                    set presenter notes of slide slideIndex to noteText
                    set skipped of slide slideIndex to (slideIndex > 6)
                end repeat
                save in (POSIX file keyPath)
            end tell
            log "Native Keynote saved"
            export sampleDeck to (POSIX file pdfPath) as PDF with properties {skipped slides:true}
            export sampleDeck to (POSIX file notesPath) as PDF with properties {export style:SlideWithNotes, skipped slides:true}
            export sampleDeck to (POSIX file roundtripPath) as Microsoft PowerPoint
            set resultText to "Saved native Keynote with " & (count of slides of sampleDeck) & " slides and presenter notes: " & keyPath
            close sampleDeck saving yes
            return resultText
        end tell
    end timeout
end run
