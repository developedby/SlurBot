"""Bot that detects slur/trigger word usage and notifies mods"""
import json
import datetime

import discord


# Put your bot's token here
#
# BE CAREFUL NOT TO SHARE IT WITH ANYONE!!
#
TOKEN = ''

# Path to the file containing all the data
# THIS FILE IS IMPORTANT SO MAKE REGULAR BACKUPS
DATA_FILE_PATH = './data.json'


# This should match with what is in execute_command
# TODO: Make these 2 parts not independent
CMD_LIST = ['add', 'remove', 'notify', 'list']

# TODO: Don't rely on this not changing in the future
LINK_PREFIX = 'https://discordapp.com/channels/'

CLIENT = discord.Client()
WORDS = None  # List of words that the bot searches for
MOD_ID = None  # ID of the mod role
PREFIX = None  # Prefix for the bot's commands
CHANNEL_ID = None  # ID of the channel where the bot sends the messages

@CLIENT.event
async def on_ready():
    """Displays a message, notifying that the bot is running.
    Executed after logging in.
    """
    print('Logged in as:')
    print(f'\tName: {CLIENT.user.name}')
    print(f'\tID:{CLIENT.user.id}')
    print('------')
    print('Slurbot is now running')
    print('-------')
    print(f'Registered words: {WORDS}')
    print(f'Mod ID: {MOD_ID}')
    print(f'Prefix: {PREFIX}')
    print(f'Channel ID: {CHANNEL_ID}')


@CLIENT.event
async def on_message(msg):
    """Executed every time a new message is sent."""
    # we do not want the bot to reply to itself
    if msg.author == CLIENT.user:
        return
    
    if is_command(msg):
        await execute_command(msg)

    elif has_word(msg):
        uncensored, censored = get_words(msg)
        await notify_mods(type_="new", msg=msg, words=(uncensored, censored))


@CLIENT.event
async def on_message_edit(before, after):
    """Executed every time a message is edited."""
    if has_word(after):
        uncensored, censored = get_words(after)
        await notify_mods(type_="edit", msg=after, words=(uncensored, censored))


async def execute_command(msg):
    """Analyses which command was sent and executes it
    if the author of the message has permission.
    """
    text = msg.content[len(PREFIX):]  # Strip the prefix
    cmd = text.split(' ')[0]
    args = text[len(cmd)+1:]

    if cmd == 'add':
        await add_word_cmd(args, msg)
    elif cmd == 'remove':
        await remove_word_cmd(args, msg)
    elif cmd == 'notify':
        await notify_cmd(args, msg)
    elif cmd == 'list':
        await list_cmd(msg)
    else:
        print(f"Tried to execute unknown command {repr(cmd)}")


async def notify_mods(type_, msg, words=None, text=None, accused_msg=None):
    """Sends a notification to the mods that one of the words was used
    or that a user sent a manual notification.

    :param type: The type of event (new message, edit, someone warned of a word use)
    :param msg: The message containing the word, or the message of the command.
    :param words: A tuple with lists of the words used, uncensored and censored, respectively.
        Only used when type is 'new' or 'edit'.
    :param text: Complimentary text to be showed.
        Only used when type is 'command-text'.
    :param accused_msg: The message that is being accused.
        Only used when type is 'command-link'.
    """
    embed = discord.Embed(timestamp=datetime.datetime.now())
    embed.add_field
    if type_ == 'new':
        embed.title = "New message with word"
        embed.add_field(
            name="Author",
            value=f'{msg.author.display_name} ({msg.author.name}#{msg.author.discriminator})',
            inline=True)
        embed.add_field(name="Channel", value=msg.channel.name, inline=True)
        embed.add_field(name="Message", value=msg.content, inline=False)
        text = str(words[0])[1:-1] if str(words[0])[1:-1] else 'None'
        embed.add_field(name="Uncensored words detected", value=text, inline=False)
        text = str(words[1])[1:-1] if str(words[1])[1:-1] else 'None'
        embed.add_field(name="Censored words detected", value=text, inline=False)
        embed.add_field(name="Link", value=f'[Click to jump]({msg.jump_url})', inline=False)

    elif type_ == 'edit':
        embed.title = "Edited message with word"
        embed.add_field(
            name="Author",
            value=f'{msg.author.display_name} ({msg.author.name}#{msg.author.discriminator})',
            inline=True)
        embed.add_field(name="Channel", value=msg.channel.name, inline=True)
        embed.add_field(name="Message", value=msg.content, inline=False)
        text = str(words[0])[1:-1] if str(words[0])[1:-1] else 'None'
        embed.add_field(name="Uncensored words detected", value=text, inline=False)
        text = str(words[1])[1:-1] if str(words[1])[1:-1] else 'None'
        embed.add_field(name="Censored words detected", value=text, inline=False)
        embed.add_field(name="Link", value=f'[Click to jump]({msg.jump_url})', inline=True)

    elif type_ == 'command-link':
        embed.title = "User warned about a message"
        embed.description = (
            "Notification sent by "
            f"{msg.author.display_name} ({msg.author.name}#{msg.author.discriminator})"
        )
        ids = list(map(int, text[len(LINK_PREFIX):].split('/')))
        accusee_ch = CLIENT.get_channel(ids[1])
        accusee_msg = await accusee_ch.fetch_message(ids[2])
        accusee = accusee_msg.author
        embed.add_field(
            name="Author",
            value=f'{accusee.display_name} ({accusee.name}#{accusee.discriminator})',
            inline=True)
        embed.add_field(name="Channel", value=accusee_ch.name, inline=True)
        embed.add_field(name="Message", value=accusee_msg.content, inline=False)
        embed.add_field(name="Link to message", value=f'[Click to jump]({text})', inline=True)
        embed.add_field(name="Link to command", value=f'[Click to jump]({msg.jump_url})', inline=True)

    elif type_ == 'command-text':
        embed.title = "User sent a notification with no link"
        embed.add_field(
            name="Author",
            value=f'{msg.author.display_name} ({msg.author.name}#{msg.author.discriminator})',
            inline=True)
        embed.add_field(name="Channel", value=msg.channel.name, inline=True)
        if not text:
            text = 'None'
        embed.add_field(name="Message", value=text, inline=False)
        embed.add_field(name="Link", value=f'[Click to jump]({msg.jump_url})', inline=True)

    else:
        raise ValueError(f"Incorrect event type {repr(type_)}. "
                         "Must be 'new', 'edit', 'command-link', or 'command-text'")

    channel = CLIENT.get_channel(CHANNEL_ID)
    await channel.send(embed=embed)


async def add_word_cmd(word, msg):
    """Adds a new word to the word list.
    Can only be used by moderators.
    """
    if not is_moderator(msg.author, msg.guild):
        await msg.channel.send(f"You need to be a moderator to use this command")
        return

    if word in WORDS:
        await msg.channel.send(f"The word {repr(word)} is already in the list")
        return

    WORDS.append(word)

    # Add word to data file
    # TODO: Don't rewrite the whole file every time
    data = None
    with open(DATA_FILE_PATH, 'r') as data_file:
        data = json.load(data_file)
    data['words'].append(word)
    with open(DATA_FILE_PATH, 'w') as data_file:
        data_file.write(json.dumps(data, sort_keys=True, indent=4))
    
    await msg.channel.send(f"The word {repr(word)} was added to the list")


async def remove_word_cmd(word, msg):
    """Removes a word from the list.
    Can only be used by moderators.
    """
    if not is_moderator(msg.author, msg.guild):
        await msg.channel.send(f"You need to be a moderator to use this command")
        return

    if word not in WORDS:
        await msg.channel.send(f"The word {repr(word)} is not on the list")
        return

    WORDS.remove(word)

    # Remove word from data file
    # TODO: Don't rewrite the whole file every time
    data = None
    with open(DATA_FILE_PATH, 'r') as data_file:
        data = json.load(data_file)
    data['words'].remove(word)
    with open(DATA_FILE_PATH, 'w') as data_file:
        data_file.write(json.dumps(data, sort_keys=True, indent=4))
    
    await msg.channel.send(f"The word {repr(word)} was removed from the list")


async def notify_cmd(arg, msg):
    """Sends a manual notification."""
    # If a message ID was given, link to that message
    try:
        id = int(arg)
    except ValueError:
        id = None
    else:
        msg_from_id = await get_msg_from_id(id, msg.channel)
        await notify_mods(type_="command-link", msg=msg, accused_msg=msg_from_id)
        return

    # If a link to the message was given, pass on the link
    msg_from_link = await get_msg_from_link(arg, msg.guild)
    if msg_from_link:
        await notify_mods(type_="command-link", msg=msg, accused_msg=msg_from_link)

    # If something else was given, link the command and pass on the message
    else:
        await notify_mods(type_="command-text", msg=msg, text=arg)


async def list_cmd(msg):
    """Shows all the words in the list.
    Can only be used by moderators
    and only on the bot's channel.
    """
    if not is_moderator(msg.author, msg.guild):
        await msg.channel.send(f"You need to be a moderator to use this command")
        return

    if msg.channel.id != CHANNEL_ID:
        await msg.channel.send(f"This command can only be used on the bot's channel")
        return

    text = "Here are the words currently registered:\n\n"
    text += str(WORDS)[1:-1]
    await msg.channel.send(text)


def is_moderator(user, guild):
    """Returns if the user has the moderator role in the guild."""
    return guild.get_role(MOD_ID) in user.roles


def is_command(msg):
    """Returns if the message is one of the bot's commands or not"""
    if msg.content.startswith(PREFIX):
        if any(msg.content.startswith(PREFIX + cmd) for cmd in CMD_LIST):
            if (any(msg.content == PREFIX + cmd for cmd in CMD_LIST)
                or any(msg.content.startswith(PREFIX + cmd + ' ') for cmd in CMD_LIST)
            ):
                return True

    return False


def has_word(msg):
    """Returns if the message has one of the words or not"""
    if any(word in msg.content for word in WORDS):
        return True
    return False


def get_words(msg):
    """Returns the censored and uncensored words in this message that are on the word list"""
    uncensored = []
    censored = []
    text_segments = msg.content.split('||')
    for idx, segment in enumerate(text_segments):
        # Even segment means uncensored
        # Odd segment means censored unless unmatched
        # TODO: Will fail in case user uses \| to escape the vertical bar
        # TODO: Also fails if there are more than 2 | (eg |||message||||)
        # Last segment being odd means unmatched ||
        if (idx % 2) and (idx != len(text_segments)-1):
            censored_segment = True
        else:
            censored_segment = False
        for word in WORDS:
            if word in segment:
                if censored_segment:
                    censored.append(word)
                else:
                    uncensored.append(word)

    return uncensored, censored


async def get_msg_from_link(link, guild):
    if not link.startswith(LINK_PREFIX):
        return None

    # Remove the prefix and try to split into the 3 ids (guild, channel, message)
    text = text[len(LINK_PREFIX):]
    ids = text.split('/')
    try:
        ids = [int(id) for id in ids]
    except ValueError:
        return None
    if len(ids) != 3:
        return None

    # Check if the first id is the guild id
    if ids[0] != guild.id:
        return None

    # Check if the second id is one of the guild's channels
    # Fetch the channel if it is
    linked_ch = None
    for ch in guild.channels:
        if ch.id == ids[1]:
            linked_ch = ch
    if not linked_ch:
        return None

    # Try to get the message from the channel using the third id
    return await get_msg_from_id(ids[2], linked_ch)


async def get_msg_from_id(id, channel):
    """Try to fetch a message from a channel.
    Return a Message if succesfull and None otherwise.
    """
    try:
        msg = await channel.fetch_message(id)
        return msg
    except discord.NotFound:
        return None
    except discord.Forbidden:
        return None
    except discord.HTTPException:
        print('Encountered HTTPException while trying to fetch a message.')
        return None


if __name__ == '__main__':
    with open(DATA_FILE_PATH, 'r') as data_file:
        data = json.load(data_file)
        MOD_ID = data["mod-id"]
        WORDS = data["words"]
        PREFIX = data["prefix"]
        CHANNEL_ID = data["channel-id"]
    CLIENT.run(TOKEN)
