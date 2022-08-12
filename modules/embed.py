import discord

from settings import EMBED_HEX_COLOR


def to_hex(hex: str):
    return int(hex, 16)


class EmbedGenerator(discord.Embed):
    """Сразу же создает ембед. В качестве ргумента json_schema передавать словарь из языка.
    В файле с языком можно сделать такую схему:
    {
        "author_icon_url": "URL",\n
        "author_url": "URL",\n
        "author_name": "str",\n
        "title": "str",\n
        "description": "str",\n
        "thumbnail": "URL",\n
        "image": "URL",\n
        "footer_text": "str",\n
        "footer_icon_url": "URL",\n
        "color": "hex color",\n
        "fields": [{
            "name": "str",\n
            "value": "str",\n
            "inline": "bool"\n
        }]\n
    }"""

    def __init__(self, json_schema: dict, *args, **kwargs):
        # Инициализация ебмеда
        super().__init__(title=json_schema.get('title', "").format(*args, **kwargs),
                         description=json_schema.get('description', "").format(*args, **kwargs),
                         color=to_hex(json_schema.get('color', EMBED_HEX_COLOR).format(*args, **kwargs)))
        # Добавление параметров
        self.set_author(icon_url=json_schema.get('author_icon_url', "").format(*args, **kwargs),
                        url=json_schema.get('author_url', "").format(*args, **kwargs),
                        name=json_schema.get('author_name', "").format(*args, **kwargs))
        self.set_thumbnail(url=json_schema.get('thumbnail', "https://g.png").format(*args, **kwargs))
        self.set_image(url=json_schema.get('image', "https://g.png").format(*args, **kwargs))
        self.set_footer(text=json_schema.get('footer_text', "").format(*args, **kwargs),
                        icon_url=json_schema.get('footer_icon_url', "https://g.png").format(*args, **kwargs))
        for field in json_schema.get("fields", []):
            self.add_field(name=field.get("name", "** **").format(*args, **kwargs),
                           value=field.get("value", "** **").format(*args, **kwargs),
                           inline=field.get("inline", True))

# embed = EmbedGenerator(
#     json_schema={
#         "title": "Привет {user_name}",
#         "fields": [
#             {"title": "",
#              "value": "",
#              "inline": True}
#         ]
#     },
#     user_name="Кирил"
# )
