import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
import json
import aiohttp

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()

class ModernBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)
        self.persistent_views_added = False
        self.reminders = []
        self.counters = {}
        self.todo_lists = {}
        self.polls = {}
        self.custom_commands = {}
        self.afk_users = {}
        self.starboard = {}
        self.auto_roles = {}
        self.welcome_messages = {}
        self.farewell_messages = {}

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = ModernBot()

# 1. Ping Command
@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")

# 2. Server Info Command
@bot.tree.command(name="serverinfo", description="Get information about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.blue())
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)

# 3. User Info Command
@bot.tree.command(name="userinfo", description="Get information about a user")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"User Information - {member.name}", color=member.color)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await interaction.response.send_message(embed=embed)

# 4. Avatar Command
@bot.tree.command(name="avatar", description="Get a user's avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"{member.name}'s Avatar")
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await interaction.response.send_message(embed=embed)

# 5. Say Command
@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.checks.has_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

# 6. Poll Command
@bot.tree.command(name="poll", description="Create a poll")
async def poll(interaction: discord.Interaction, question: str, options: str):
    options_list = options.split(',')
    if len(options_list) < 2 or len(options_list) > 10:
        await interaction.response.send_message("Please provide 2-10 options separated by commas.", ephemeral=True)
        return

    embed = discord.Embed(title="Poll", description=question, color=discord.Color.blue())
    for i, option in enumerate(options_list):
        embed.add_field(name=f"Option {i+1}", value=option.strip(), inline=False)

    poll_msg = await interaction.channel.send(embed=embed)
    bot.polls[poll_msg.id] = len(options_list)

    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    for i in range(len(options_list)):
        await poll_msg.add_reaction(emojis[i])

    await interaction.response.send_message("Poll created!", ephemeral=True)

# 7. Reminder Command
@bot.tree.command(name="remind", description="Set a reminder")
async def remind(interaction: discord.Interaction, time: str, *, message: str):
    try:
        duration = int(time[:-1])
        unit = time[-1].lower()
        if unit == 'm':
            delta = timedelta(minutes=duration)
        elif unit == 'h':
            delta = timedelta(hours=duration)
        elif unit == 'd':
            delta = timedelta(days=duration)
        else:
            raise ValueError
        
        reminder_time = datetime.utcnow() + delta
        bot.reminders.append({
            'user_id': interaction.user.id,
            'channel_id': interaction.channel_id,
            'time': reminder_time,
            'message': message
        })
        await interaction.response.send_message(f"I'll remind you about '{message}' in {time}.")
    except ValueError:
        await interaction.response.send_message("Invalid time format. Use a number followed by 'm' for minutes, 'h' for hours, or 'd' for days. For example: 30m, 2h, 1d")

# 8. Todo List Command
@bot.tree.command(name="todo", description="Manage your todo list")
async def todo(interaction: discord.Interaction, action: str, item: str = None):
    user_id = str(interaction.user.id)
    if user_id not in bot.todo_lists:
        bot.todo_lists[user_id] = []

    if action.lower() == "add" and item:
        bot.todo_lists[user_id].append(item)
        await interaction.response.send_message(f"Added '{item}' to your todo list.")
    elif action.lower() == "remove" and item:
        if item in bot.todo_lists[user_id]:
            bot.todo_lists[user_id].remove(item)
            await interaction.response.send_message(f"Removed '{item}' from your todo list.")
        else:
            await interaction.response.send_message(f"'{item}' not found in your todo list.")
    elif action.lower() == "list":
        if bot.todo_lists[user_id]:
            todo_list = "\n".join(f"{i+1}. {task}" for i, task in enumerate(bot.todo_lists[user_id]))
            await interaction.response.send_message(f"Your todo list:\n{todo_list}")
        else:
            await interaction.response.send_message("Your todo list is empty.")
    else:
        await interaction.response.send_message("Invalid action. Use 'add', 'remove', or 'list'.")

# 9. Random Choice Command
@bot.tree.command(name="choose", description="Make a random choice")
async def choose(interaction: discord.Interaction, choices: str):
    options = [choice.strip() for choice in choices.split(',')]
    if len(options) < 2:
        await interaction.response.send_message("Please provide at least two choices separated by commas.")
    else:
        chosen = random.choice(options)
        await interaction.response.send_message(f"I choose: {chosen}")

# 10. Coin Flip Command
@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    result = random.choice(["Heads", "Tails"])
    await interaction.response.send_message(f"The coin landed on: {result}")

# 11. Roll Dice Command
@bot.tree.command(name="roll", description="Roll dice (e.g., 2d6)")
async def roll(interaction: discord.Interaction, dice: str):
    try:
        num_dice, num_sides = map(int, dice.lower().split('d'))
        if num_dice > 100 or num_sides > 100:
            await interaction.response.send_message("Please use a reasonable number of dice and sides (max 100 each).")
            return
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls)
        await interaction.response.send_message(f"Rolls: {rolls}\nTotal: {total}")
    except ValueError:
        await interaction.response.send_message("Invalid dice format. Use 'NdM' where N is the number of dice and M is the number of sides.")

# 12. Welcome Message Setup
@bot.tree.command(name="set_welcome", description="Set up a welcome message")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    bot.welcome_messages[interaction.guild.id] = {"channel": channel.id, "message": message}
    await interaction.response.send_message(f"Welcome message set in {channel.mention}")

# 13. Farewell Message Setup
@bot.tree.command(name="set_farewell", description="Set up a farewell message")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_farewell(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    bot.farewell_messages[interaction.guild.id] = {"channel": channel.id, "message": message}
    await interaction.response.send_message(f"Farewell message set in {channel.mention}")

# 14. Member Counter
@bot.tree.command(name="member_count", description="Display the current member count")
async def member_count(interaction: discord.Interaction):
    await interaction.response.send_message(f"Current member count: {interaction.guild.member_count}")

# 15. Purge Messages
@bot.tree.command(name="purge", description="Delete a specified number of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Please specify a number between 1 and 100.")
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

# 16. Server Rules
@bot.tree.command(name="rules", description="Display server rules")
@app_commands.checks.has_permissions(manage_guild=True)
async def rules(interaction: discord.Interaction, *, rules_text: str):
    embed = discord.Embed(title="Server Rules", description=rules_text, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

# 17. Reaction Roles Setup
class ReactionRoleView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="Get Role", style=discord.ButtonStyle.primary, custom_id="get_role")
    async def get_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            await interaction.response.send_message(f"Removed {self.role.name} role.", ephemeral=True)
        else:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(f"Added {self.role.name} role.", ephemeral=True)

@bot.tree.command(name="setup_reaction_role", description="Set up a reaction role")
@app_commands.checks.has_permissions(manage_roles=True)
async def setup_reaction_role(interaction: discord.Interaction, role: discord.Role):
    view = ReactionRoleView(role)
    await interaction.response.send_message(f"Click the button to get or remove the {role.name} role:", view=view)

# 18. Ticket System
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        existing_ticket = discord.utils.get(guild.text_channels, name=f'ticket-{member.id}')
        
        if existing_ticket:
            await interaction.response.send_message(f"You already have an open ticket: {existing_ticket.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        channel = await guild.create_text_channel(f'ticket-{member.id}', overwrites=overwrites, category=interaction.channel.category)
        await channel.send(f"{member.mention} has created a ticket. Staff will be with you shortly.")
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.tree.command(name="setup_ticket_system", description="Set up the ticket system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_ticket_system(interaction: discord.Interaction):
    embed = discord.Embed(title="Support Ticket System", description="Click the button below to create a support ticket.")
    view = TicketView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Ticket system set up successfully!", ephemeral=True)

# 19. Custom Commands

@bot.tree.command(name="add_command", description="Add a custom command")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_command(interaction: discord.Interaction, command_name: str, response: str):
    bot.custom_commands[command_name] = response
    await interaction.response.send_message(f"Custom command '{command_name}' added successfully.")

@bot.tree.command(name="remove_command", description="Remove a custom command")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_command(interaction: discord.Interaction, command_name: str):
    if command_name in bot.custom_commands:
        del bot.custom_commands[command_name]
        await interaction.response.send_message(f"Custom command '{command_name}' removed successfully.")
    else:
        await interaction.response.send_message(f"Custom command '{command_name}' not found.")

# 20. Giveaway System
class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.entries = set()

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.green, custom_id="enter_giveaway")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.entries.add(interaction.user.id)
        await interaction.response.send_message("You've entered the giveaway!", ephemeral=True)

@bot.tree.command(name="start_giveaway", description="Start a giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
async def start_giveaway(interaction: discord.Interaction, duration: int, prize: str):
    embed = discord.Embed(title="Giveaway!", description=f"Prize: {prize}\nDuration: {duration} minutes", color=discord.Color.gold())
    view = GiveawayView()
    message = await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Giveaway started!", ephemeral=True)

    await asyncio.sleep(duration * 60)
    
    if view.entries:
        winner_id = random.choice(list(view.entries))
        winner = interaction.guild.get_member(winner_id)
        await interaction.channel.send(f"Congratulations {winner.mention}! You won the giveaway for {prize}!")
    else:
        await interaction.channel.send("No one entered the giveaway.")

# 21. AFK System
@bot.tree.command(name="afk", description="Set your AFK status")
async def afk(interaction: discord.Interaction, reason: str = "AFK"):
    bot.afk_users[interaction.user.id] = reason
    await interaction.response.send_message(f"{interaction.user.mention} is now AFK: {reason}")

# 22. Starboard
@bot.tree.command(name="setup_starboard", description="Set up a starboard channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def setup_starboard(interaction: discord.Interaction, channel: discord.TextChannel, threshold: int = 3):
    bot.starboard[interaction.guild.id] = {"channel": channel.id, "threshold": threshold}
    await interaction.response.send_message(f"Starboard set up in {channel.mention} with a threshold of {threshold} stars.")

# 23. Auto Role
@bot.tree.command(name="set_auto_role", description="Set a role to be automatically assigned to new members")
@app_commands.checks.has_permissions(manage_roles=True)
async def set_auto_role(interaction: discord.Interaction, role: discord.Role):
    bot.auto_roles[interaction.guild.id] = role.id
    await interaction.response.send_message(f"Auto role set to {role.name}")

# 24. Server Stats
@bot.tree.command(name="server_stats", description="Display server statistics")
async def server_stats(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Statistics", color=discord.Color.blue())
    embed.add_field(name="Total Members", value=guild.member_count, inline=True)
    embed.add_field(name="Online Members", value=sum(1 for m in guild.members if m.status != discord.Status.offline), inline=True)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    await interaction.response.send_message(embed=embed)

# 25. Role Info
@bot.tree.command(name="roleinfo", description="Get information about a role")
async def roleinfo(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(title=f"Role Information: {role.name}", color=role.color)
    embed.add_field(name="ID", value=role.id, inline=True)
    embed.add_field(name="Created At", value=role.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Members", value=len(role.members), inline=True)
    embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
    embed.add_field(name="Hoisted", value=role.hoist, inline=True)
    embed.add_field(name="Position", value=role.position, inline=True)
    await interaction.response.send_message(embed=embed)

# 26. Emoji Info
@bot.tree.command(name="emojiinfo", description="Get information about an emoji")
async def emojiinfo(interaction: discord.Interaction, emoji: discord.Emoji):
    embed = discord.Embed(title=f"Emoji Information: {emoji.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=emoji.id, inline=True)
    embed.add_field(name="Created At", value=emoji.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Animated", value=emoji.animated, inline=True)
    embed.add_field(name="Available", value=emoji.available, inline=True)
    embed.set_thumbnail(url=emoji.url)
    await interaction.response.send_message(embed=embed)

# 27. Channel Info
@bot.tree.command(name="channelinfo", description="Get information about a channel")
async def channelinfo(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    embed = discord.Embed(title=f"Channel Information: {channel.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=channel.id, inline=True)
    embed.add_field(name="Created At", value=channel.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
    embed.add_field(name="Topic", value=channel.topic or "No topic set", inline=False)
    await interaction.response.send_message(embed=embed)

# 28. Server Icon
@bot.tree.command(name="servericon", description="Get the server's icon")
async def servericon(interaction: discord.Interaction):
    if interaction.guild.icon:
        embed = discord.Embed(title=f"{interaction.guild.name}'s Icon")
        embed.set_image(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("This server doesn't have an icon.")

# 29. User Banner
@bot.tree.command(name="banner", description="Get a user's banner")
async def banner(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    user = await bot.fetch_user(member.id)
    if user.banner:
        embed = discord.Embed(title=f"{user.name}'s Banner")
        embed.set_image(url=user.banner.url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("This user doesn't have a banner.")

# 30. Invite Info
@bot.tree.command(name="inviteinfo", description="Get information about an invite")
async def inviteinfo(interaction: discord.Interaction, invite_code: str):
    try:
        invite = await bot.fetch_invite(invite_code)
        embed = discord.Embed(title="Invite Information", color=discord.Color.blue())
        embed.add_field(name="Server", value=invite.guild.name, inline=True)
        embed.add_field(name="Channel", value=invite.channel.name, inline=True)
        embed.add_field(name="Inviter", value=invite.inviter.name if invite.inviter else "Unknown", inline=True)
        embed.add_field(name="Max Uses", value=invite.max_uses if invite.max_uses else "Unlimited", inline=True)
        embed.add_field(name="Expires At", value=invite.expires_at.strftime("%Y-%m-%d %H:%M:%S") if invite.expires_at else "Never", inline=True)
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("Invalid invite code.")

# 31. Message Info
@bot.tree.command(name="messageinfo", description="Get information about a message")
async def messageinfo(interaction: discord.Interaction, message_id: str):
    try:
        message = await interaction.channel.fetch_message(int(message_id))
        embed = discord.Embed(title="Message Information", color=discord.Color.blue())
        embed.add_field(name="Author", value=message.author.name, inline=True)
        embed.add_field(name="Created At", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Edited At", value=message.edited_at.strftime("%Y-%m-%d %H:%M:%S") if message.edited_at else "Not edited", inline=True)
        embed.add_field(name="Content", value=message.content[:1024] if message.content else "No content", inline=False)
        embed.add_field(name="Attachments", value=len(message.attachments), inline=True)
        embed.add_field(name="Embeds", value=len(message.embeds), inline=True)
        await interaction.response.send_message(embed=embed)
    except discord.NotFound:
        await interaction.response.send_message("Message not found.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check for AFK users
    if message.author.id in bot.afk_users:
        del bot.afk_users[message.author.id]
        await message.channel.send(f"Welcome back, {message.author.mention}! I've removed your AFK status.")

    for member in message.mentions:
        if member.id in bot.afk_users:
            await message.channel.send(f"{member.name} is AFK: {bot.afk_users[member.id]}")

    # Check for custom commands
    if message.content.startswith('!'):
        command_name = message.content[1:].lower()
        if command_name in bot.custom_commands:
            await message.channel.send(bot.custom_commands[command_name])

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    # Starboard functionality
    if reaction.emoji == "⭐" and reaction.message.guild.id in bot.starboard:
        starboard_info = bot.starboard[reaction.message.guild.id]
        if reaction.count >= starboard_info["threshold"]:
            starboard_channel = reaction.message.guild.get_channel(starboard_info["channel"])
            if starboard_channel:
                embed = discord.Embed(description=reaction.message.content, color=discord.Color.gold())
                embed.set_author(name=reaction.message.author.name, icon_url=reaction.message.author.avatar.url)
                embed.add_field(name="Original", value=f"[Jump to message]({reaction.message.jump_url})")
                embed.set_footer(text=f"⭐ {reaction.count} | {reaction.message.channel.name}")
                if reaction.message.attachments:
                    embed.set_image(url=reaction.message.attachments[0].url)
                await starboard_channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    # Auto role
    if member.guild.id in bot.auto_roles:
        role = member.guild.get_role(bot.auto_roles[member.guild.id])
        if role:
            await member.add_roles(role)

    # Welcome message
    if member.guild.id in bot.welcome_messages:
        welcome_info = bot.welcome_messages[member.guild.id]
        channel = member.guild.get_channel(welcome_info["channel"])
        if channel:
            await channel.send(welcome_info["message"].format(member=member))

@bot.event
async def on_member_remove(member):
    # Farewell message
    if member.guild.id in bot.farewell_messages:
        farewell_info = bot.farewell_messages[member.guild.id]
        channel = member.guild.get_channel(farewell_info["channel"])
        if channel:
            await channel.send(farewell_info["message"].format(member=member))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    if not bot.persistent_views_added:
        bot.add_view(TicketView())
        bot.persistent_views_added = True

    check_reminders.start()

@tasks.loop(seconds=60)
async def check_reminders():
    current_time = datetime.utcnow()
    reminders_to_remove = []
    for reminder in bot.reminders:
        if current_time >= reminder['time']:
            channel = bot.get_channel(reminder['channel_id'])
            user = bot.get_user(reminder['user_id'])
            if channel and user:
                await channel.send(f"{user.mention}, here's your reminder: {reminder['message']}")
            reminders_to_remove.append(reminder)
    for reminder in reminders_to_remove:
        bot.reminders.remove(reminder)

# Run the bot
bot.run(TOKEN)