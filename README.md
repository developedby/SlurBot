# slurbot

A discord bot that warns moderators of slur and trigger words usage

Made for discord.py version 1.3.3
Requires python >= 3.5.3

To run:

* In `bot.py`, insert your bot token in the TOKEN variable
* Insert the path to your data file in the DATA_FILE_PATH variable
* Run `bot.py`

The data file needs to be a json file with the following fields:

* `"prefix"` - The prefix for the bot's commands (eg: `"sb!"` searches for messages like `sb!add`)
* `"words"` - The list of words that the bot searches in messages
* `"mod-id"` - The ID of the role allowed to use the bot-managing commands (add and remove, but not notify)
* `"channel-id"` - The ID of the channel where the bot sends the notifications

The following commands are available:

* `add` - Adds a word to the list. Eg: `sb!add fuck`
* `remove` - Removes a word from the list. Eg: `sb!remove fuck`
* `notify` - Manually triggers a notification. It accepts 3 types of arguments:
    * A message id of a message sent in the same channel as the command. Eg: `sb!notify 734987398173`
    * A link to a message. Eg: `sb!notify https://discordapp.com/channels/6339019/6543744587/72472384860`
    * Some text. In this case, the notification message points to the command message, and this text is shown with it. Eg: `sb!notify The person above me said fuck`
* `list` - Shows all the words in the list. Can only be used by moderators and only on the bot's channel.

The bot checks both for sent messages and for edited messages.