import discord
from discord.ext import commands
import random
import json
import asyncio

import os
TOKEN = os.getenv("TOKEN")

DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

cars = [
    "Ferrari 296 GT3",
    "BMW M4 GT3",
    "Porsche 911 GT3 R",
    "Mercedes AMG GT3",
    "Lamborghini Huracan GT3",
    "Audi R8 LMS GT3",
    "McLaren 720S GT3",
    "Aston Martin Vantage GT3",
    "Bentley Continental GT3",
    "Honda NSX GT3",
    "Nissan GTR GT3",
    "Lexus RC F GT3"
]

tracks = [
    "Monza",
    "Spa",
    "Mount Panorama",
    "Brands Hatch",
    "Misano",
    "Silverstone",
    "Barcelona",
    "Nurburgring",
    "Paul Ricard",
    "Zolder"
]

weather_options = [
    "Sereno",
    "Nuvoloso",
    "Pioggia leggera",
    "Pioggia media",
    "Meteo variabile"
]

time_options = [
    "Mattina",
    "Pomeriggio",
    "Tramonto",
    "Sera",
    "Notte"
]

chaos_options = [
    "Nessuna regola speciale",
    "Pit obbligatorio",
    "i primi 5 della Q partono dai box",
    "primo giro in ghostmode",
    "Meteo casuale attivo",
    "Orario serale obbligatorio"
]


def default_data():
    return {
        "drivers": [],
        "reserves": [],
        "iscrizioni_aperte": True,
        "pista_estratta": None,
        "meteo_estratto": None,
        "orario_estratto": None,
        "chaos_rule": None
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(default_data())
        return default_data()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def trova_driver(data, user_id):
    for d in data["drivers"]:
        if d["user_id"] == user_id:
            return d
    return None


def trova_riserva(data, user_id):
    for r in data["reserves"]:
        if r["user_id"] == user_id:
            return r
    return None


def chunk_lines(lines, max_len=1000):
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks


def build_lista_embed():
    data = load_data()

    embed = discord.Embed(
        title="📋 Lista Iscritti - DMC Manufacturer Chaos",
        description=f"Piloti principali: {len(data['drivers'])}/30",
        color=discord.Color.blue()
    )

    if data["drivers"]:
        driver_lines = [f"{i}. {d['name']}" for i, d in enumerate(data["drivers"], start=1)]
        for index, chunk in enumerate(chunk_lines(driver_lines), start=1):
            nome = "Iscritti" if index == 1 else f"Iscritti ({index})"
            embed.add_field(name=nome, value=chunk, inline=False)
    else:
        embed.add_field(name="Iscritti", value="Nessuno", inline=False)

    if data["reserves"]:
        reserve_lines = [f"R{i}. {r['name']}" for i, r in enumerate(data["reserves"], start=1)]
        for index, chunk in enumerate(chunk_lines(reserve_lines), start=1):
            nome = "Riserve" if index == 1 else f"Riserve ({index})"
            embed.add_field(name=nome, value=chunk, inline=False)

    embed.set_footer(text="DMC Chaos Bot")
    return embed


def build_entrylist_embed():
    data = load_data()

    embed = discord.Embed(
        title="🏁 Entry List - DMC Chaos Event",
        color=discord.Color.gold()
    )

    info = [
        f"**Pista:** {data['pista_estratta'] if data['pista_estratta'] else 'Da estrarre'}",
        f"**Meteo:** {data['meteo_estratto'] if data['meteo_estratto'] else 'Da estrarre'}",
        f"**Orario:** {data['orario_estratto'] if data['orario_estratto'] else 'Da estrarre'}",
        f"**Regola Chaos:** {data['chaos_rule'] if data['chaos_rule'] else 'Da estrarre'}"
    ]
    embed.description = "\n".join(info)

    if data["drivers"]:
        driver_lines = []
        for i, d in enumerate(data["drivers"], start=1):
            car = d["car"] if d["car"] else "Auto non assegnata"
            driver_lines.append(f"{i}. {d['name']} — {car}")

        for index, chunk in enumerate(chunk_lines(driver_lines), start=1):
            nome = "Piloti" if index == 1 else f"Piloti ({index})"
            embed.add_field(name=nome, value=chunk, inline=False)
    else:
        embed.add_field(name="Piloti", value="Nessuno", inline=False)

    if data["reserves"]:
        reserve_lines = []
        for i, r in enumerate(data["reserves"], start=1):
            car = r["car"] if r["car"] else "Auto non assegnata"
            reserve_lines.append(f"R{i}. {r['name']} — {car}")

        for index, chunk in enumerate(chunk_lines(reserve_lines), start=1):
            nome = "Riserve" if index == 1 else f"Riserve ({index})"
            embed.add_field(name=nome, value=chunk, inline=False)

    embed.set_footer(text="DMC Chaos Bot")
    return embed


class ChaosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iscriviti", style=discord.ButtonStyle.success, custom_id="chaos_iscriviti")
    async def iscriviti_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()

        if not data["iscrizioni_aperte"]:
            await interaction.response.send_message("❌ Iscrizioni chiuse.", ephemeral=True)
            return

        user_id = interaction.user.id
        nome = interaction.user.display_name

        if trova_driver(data, user_id):
            await interaction.response.send_message("⚠️ Sei già iscritto.", ephemeral=True)
            return

        if trova_riserva(data, user_id):
            await interaction.response.send_message("⚠️ Sei già nelle riserve.", ephemeral=True)
            return

        entry = {
            "user_id": user_id,
            "name": nome,
            "car": None
        }

        if len(data["drivers"]) < 30:
            data["drivers"].append(entry)
            save_data(data)
            await interaction.response.send_message(
                f"✅ {nome} iscritto! ({len(data['drivers'])}/30)",
                ephemeral=True
            )
        else:
            data["reserves"].append(entry)
            save_data(data)
            await interaction.response.send_message(
                f"🟡 {nome} aggiunto alle riserve (R{len(data['reserves'])})",
                ephemeral=True
            )

    @discord.ui.button(label="Lascia", style=discord.ButtonStyle.danger, custom_id="chaos_lascia")
    async def lascia_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()

        user_id = interaction.user.id
        nome = interaction.user.display_name

        d = trova_driver(data, user_id)
        if d:
            data["drivers"].remove(d)

            promoted_name = None
            if data["reserves"]:
                nuovo = data["reserves"].pop(0)
                data["drivers"].append(nuovo)
                promoted_name = nuovo["name"]

            save_data(data)

            msg = f"🗑️ {nome} rimosso dalla lista."
            if promoted_name:
                msg += f"\n⬆️ {promoted_name} promosso dalla riserva."

            await interaction.response.send_message(msg, ephemeral=True)
            return

        r = trova_riserva(data, user_id)
        if r:
            data["reserves"].remove(r)
            save_data(data)
            await interaction.response.send_message("🗑️ Sei stato rimosso dalle riserve.", ephemeral=True)
            return

        await interaction.response.send_message("❌ Non sei iscritto.", ephemeral=True)

    @discord.ui.button(label="Lista", style=discord.ButtonStyle.primary, custom_id="chaos_lista")
    async def lista_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=build_lista_embed(), ephemeral=True)

    @discord.ui.button(label="Entry List", style=discord.ButtonStyle.secondary, custom_id="chaos_entrylist")
    async def entrylist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=build_entrylist_embed(), ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(ChaosView())
    load_data()
    print(f"Bot online come {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def pannello(ctx):
    embed = discord.Embed(
        title="🚨 DMC MANUFACTURER CHAOS 🚨",
        description="Usa i pulsanti qui sotto per gestire l'iscrizione all'evento.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="Format",
        value=(
            "Assetto Corsa Competizione\n"
            "10 min PL 15 min Q 40 min gara\n"
            "apertura server ore 20:00...estrazione in live alle 14:00"
        ),
        inline=False
    )

    embed.add_field(
        name="Live Draw",
        value=(
            "• estrazione pista\n"
            "• assegnazione auto ai piloti\n"
            "• meteo / orario / regola chaos"
        ),
        inline=False
    )

    embed.add_field(
        name="Slot",
        value="Max 30 piloti + riserve",
        inline=False
    )

    embed.set_footer(text="DMC Chaos Bot")

    await ctx.send(embed=embed, view=ChaosView())


@bot.command()
async def lista(ctx):
    await ctx.send(embed=build_lista_embed())


@bot.command()
async def entrylist(ctx):
    await ctx.send(embed=build_entrylist_embed())


@bot.command()
@commands.has_permissions(administrator=True)
async def apriiscrizioni(ctx):
    data = load_data()
    data["iscrizioni_aperte"] = True
    save_data(data)
    await ctx.send("🟢 Iscrizioni aperte!")


@bot.command()
@commands.has_permissions(administrator=True)
async def chiudiiscrizioni(ctx):
    data = load_data()
    data["iscrizioni_aperte"] = False
    save_data(data)
    await ctx.send("🔴 Iscrizioni chiuse.")


@bot.command()
@commands.has_permissions(administrator=True)
async def assegnaauto(ctx):
    data = load_data()

    if len(data["drivers"]) == 0 and len(data["reserves"]) == 0:
        await ctx.send("❌ Nessun pilota.")
        return

    pool = cars.copy()
    random.shuffle(pool)

    for i, d in enumerate(data["drivers"]):
        d["car"] = pool[i] if i < len(pool) else random.choice(cars)

    random.shuffle(pool)
    for i, r in enumerate(data["reserves"]):
        r["car"] = pool[i] if i < len(pool) else random.choice(cars)

    save_data(data)
    await ctx.send("🏁 Auto assegnate a tutta la lista completa.")


@bot.command()
@commands.has_permissions(administrator=True)
async def estrazionepista(ctx):
    data = load_data()
    data["pista_estratta"] = random.choice(tracks)
    save_data(data)
    await ctx.send(f"🎲 Pista estratta: **{data['pista_estratta']}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def estrazionemeteo(ctx):
    data = load_data()
    data["meteo_estratto"] = random.choice(weather_options)
    save_data(data)
    await ctx.send(f"🌦️ Meteo estratto: **{data['meteo_estratto']}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def estrazioneorario(ctx):
    data = load_data()
    data["orario_estratto"] = random.choice(time_options)
    save_data(data)
    await ctx.send(f"🕒 Orario estratto: **{data['orario_estratto']}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def ruotadelcaos(ctx):
    data = load_data()
    data["chaos_rule"] = random.choice(chaos_options)
    save_data(data)
    await ctx.send(f"🎡 Ruota del Chaos: **{data['chaos_rule']}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    save_data(default_data())
    await ctx.send("♻️ Evento resettato.")


@pannello.error
@apriiscrizioni.error
@chiudiiscrizioni.error
@assegnaauto.error
@estrazionepista.error
@estrazionemeteo.error
@estrazioneorario.error
@ruotadelcaos.error
@reset.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Non hai i permessi admin per usare questo comando.")

@bot.command()
@commands.has_permissions(administrator=True)
async def liveroulette(ctx):
    data = load_data()

    pista_finale = random.choice(tracks)
    meteo_finale = random.choice(weather_options)
    orario_finale = random.choice(time_options)
    chaos_finale = random.choice(chaos_options)

    msg = await ctx.send("🎰 **LIVE CHAOS ROULETTE**\nPreparazione estrazione...")

    # PISTA
    for i in range(10):
        pista = random.choice(tracks)
        await msg.edit(
            content=f"🎰 **LIVE CHAOS ROULETTE**\n\n🏁 Pista: **{pista}**"
        )
        await asyncio.sleep(0.20 + i * 0.04)

    await msg.edit(
        content=f"🎰 **LIVE CHAOS ROULETTE**\n\n🏁 Pista: **{pista_finale}**"
    )
    await asyncio.sleep(0.8)

    # METEO
    for i in range(10):
        meteo = random.choice(weather_options)
        await msg.edit(
            content=(
                f"🎰 **LIVE CHAOS ROULETTE**\n\n"
                f"🏁 Pista: **{pista_finale}**\n"
                f"🌦️ Meteo: **{meteo}**"
            )
        )
        await asyncio.sleep(0.20 + i * 0.04)

    await msg.edit(
        content=(
            f"🎰 **LIVE CHAOS ROULETTE**\n\n"
            f"🏁 Pista: **{pista_finale}**\n"
            f"🌦️ Meteo: **{meteo_finale}**"
        )
    )
    await asyncio.sleep(0.8)

    # ORARIO
    for i in range(10):
        orario = random.choice(time_options)
        await msg.edit(
            content=(
                f"🎰 **LIVE CHAOS ROULETTE**\n\n"
                f"🏁 Pista: **{pista_finale}**\n"
                f"🌦️ Meteo: **{meteo_finale}**\n"
                f"🕒 Orario: **{orario}**"
            )
        )
        await asyncio.sleep(0.20 + i * 0.04)

    await msg.edit(
        content=(
            f"🎰 **LIVE CHAOS ROULETTE**\n\n"
            f"🏁 Pista: **{pista_finale}**\n"
            f"🌦️ Meteo: **{meteo_finale}**\n"
            f"🕒 Orario: **{orario_finale}**"
        )
    )
    await asyncio.sleep(0.8)

    # CHAOS
    for i in range(10):
        regola = random.choice(chaos_options)
        await msg.edit(
            content=(
                f"🎰 **LIVE CHAOS ROULETTE**\n\n"
                f"🏁 Pista: **{pista_finale}**\n"
                f"🌦️ Meteo: **{meteo_finale}**\n"
                f"🕒 Orario: **{orario_finale}**\n"
                f"🎡 Chaos: **{regola}**"
            )
        )
        await asyncio.sleep(0.20 + i * 0.04)

    data["pista_estratta"] = pista_finale
    data["meteo_estratto"] = meteo_finale
    data["orario_estratto"] = orario_finale
    data["chaos_rule"] = chaos_finale
    save_data(data)

    await msg.edit(
        content=(
            f"🏆 **RISULTATO FINALE LIVE CHAOS ROULETTE**\n\n"
            f"🏁 Pista: **{pista_finale}**\n"
            f"🌦️ Meteo: **{meteo_finale}**\n"
            f"🕒 Orario: **{orario_finale}**\n"
            f"🎡 Regola Chaos: **{chaos_finale}**"
        )
    )

bot.run(TOKEN)
