def panel_frame(w, h, title):
    pn = np.zeros((h, w, 4), np.uint8); im = Image.fromarray(pn); d = ImageDraw.Draw(im)
    d.rectangle((5, 5, w - 6, h - 6), fill=(8, 48, 78, 170), outline=(120, 230, 255, 245), width=4)
    for y in range(10, h - 8, 6): d.line((9, y, w - 9, y), fill=(120, 230, 255, 14), width=2)
    pn = np.array(im); ts = text_sprite(title, 40, (224, 248, 255, 255), glow=(95, 216, 255), glow_r=8, spacing=3, pad=30)
    over(pn, ts, 30 + ts.shape[1] / 2 - 30 + 4, 46); return pn

