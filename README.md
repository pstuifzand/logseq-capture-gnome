# logseq-capture-gnome

This is a Python script that shows a textarea with which you can capture a note for Logseq.

This uses the Logseq HTTP API to send a note to Logseq.

You can use `Escape` to close the window without sending a note. And you can use `<Control>Return` to
send the note to Logseq.

It uses the file `~/.config/logseq-capture/config.json` for configuration variables.
There is one variable `LOGSEQ_TOKEN`. This should contain the token you set in the API keys configuration in Logseq.
