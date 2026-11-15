
EMOJIS = [
 (.9, 3.6, '🇲🇽', 880, 520, 165, 'pop'), (1.2, 9.8, '☢️', 220, 400, 185, 'late'), (7.9, 10.25, '💥', 860, 800, 195, 'sacude'),
 (11.4, 15.0, '📜', 215, 1150, 160, 'flota'), (12.0, 16.0, '❌', 860, 880, 155, 'sacude'), (16.1, 18.6, '🕊️', 860, 880, 165, 'flota'), (20.2, 23.6, '⚠️', 860, 880, 170, 'late'),
 (26.9, 30.5, '🇺🇸', 170, 1330, 165, 'pop'), (30.7, 33.2, '🚫', 910, 1330, 160, 'sacude'), (34.6, 37.1, '💸', 180, 735, 160, 'flota'), (35.7, 37.1, '📉', 900, 735, 160, 'cae'),
 (38.3, 43.9, '📉', 900, 1480, 140, 'sacude'), (42.3, 44.2, '💰', 680, 1480, 140, 'late'), (44.4, 48.5, '🏥', 680, 1480, 140, 'pop'), (44.9, 48.5, '🚓', 900, 1480, 140, 'pop'),
 (53.2, 56.6, '🕊️', 230, 560, 175, 'flota'), (53.4, 54.95, '🤝', 870, 1250, 165, 'pop'), (55.0, 57.7, '💬', 870, 1250, 165, 'late'), (57.9, 60, '🔔', 870, 1250, 175, 'sacude'), (57.9, 60, '👍', 230, 560, 165, 'pop'),
]
def emoji_sprite(e):
    f = font(109, EMO); im = Image.new('RGBA', (220, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((20, 15), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); s = max(im.size) + 8
    sq = Image.new('RGBA', (s, s), (0, 0, 0, 0)); sq.paste(im, ((s - im.size[0]) // 2, (s - im.size[1]) // 2))
    return np.array(sq)

def draw_overlays(fr, T, subs, emos):
    for t0, t1, e, x, y, tam, anim, spr in emos:
        if t0 <= T < t1:
            lt = T - t0; sc = eBack(lt / .28) * tam / spr.shape[0]; op = cl((t1 - T) / .2); dx = dy = 0
            if anim == 'flota': dy = math.sin(lt * 2.4) * 14
            elif anim == 'sacude': dx = math.sin(lt * 26) * 9 * (1 if lt < 1.2 else .35)
            elif anim == 'late': sc *= 1 + .08 * math.sin(lt * 7)
            elif anim == 'cae': dy = -160 * (1 - eOut(lt / .5)) + 60 * ss(.6, 2.2, lt)
            blit(fr, spr, x + dx, y + dy, op, sc)
    for t0, t1, y, spr in subs:
        if t0 <= T < t1:
            lt = T - t0
            blit(fr, spr, 530, y, cl(lt / .07), lerp(.84, 1, eBack(lt / .16)))

