import asyncio, random, re, websockets
from websockets.exceptions import ConnectionClosed

IRC_URL = "wss://irc-ws.chat.twitch.tv:443"
TAG_RE = re.compile(r"^@(?P<tags>[^ ]+) :(?P<prefix>[^ ]+) (?P<cmd>\w+) (?P<params>.+)$")
PRIVMSG_RE = re.compile(r"^:(?P<prefix>[^ ]+) PRIVMSG #(?P<channel>\w+) :(?P<text>.*)$")

def parse_tags(tag_str: str):
    tags = {}
    for part in tag_str.split(';'):
        k, _, v = part.partition('=')
        tags[k] = v
    return tags

def is_subscriber(tags: dict) -> bool:
    badges = tags.get('badges') or ''
    return any(seg.startswith('subscriber/') for seg in badges.split(',')) if badges else False

class TwitchIRCClient:
    def __init__(self, channel: str):
        self.channel = channel.lstrip('#').lower()
        self.nick = f"justinfan{random.randint(10000,99999)}"

    async def _send(self, ws, line: str):
        await ws.send(line + "\r\n")

    async def stream(self):
        while True:
            try:
                async with websockets.connect(IRC_URL) as ws:
                    await self._send(ws, "PASS SCHMOOPIIE")
                    await self._send(ws, f"NICK {self.nick}")
                    await self._send(ws, f"JOIN #{self.channel}")
                    await self._send(ws, "CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
                    while True:
                        raw = await ws.recv()
                        for line in raw.split("\r\n"):
                            if not line: continue
                            if line.startswith("PING"):
                                await self._send(ws, "PONG :tmi.twitch.tv"); continue
                            if line.startswith('@'):
                                m = TAG_RE.match(line)
                                if m and m.group('cmd') == 'PRIVMSG':
                                    tags = parse_tags(m.group('tags'))
                                    nick = m.group('prefix').split('!')[0]
                                    params = m.group('params')
                                    text = params.split(' :',1)[1] if ' :' in params else ''
                                    yield nick, text, is_subscriber(tags)
                                    continue
                            m2 = PRIVMSG_RE.match(line)
                            if m2:
                                nick = m2.group('prefix').split('!')[0]
                                text = m2.group('text')
                                yield nick, text, False
            except ConnectionClosed:
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(2)
