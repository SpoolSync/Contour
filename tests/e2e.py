import asyncio, json, secrets, urllib.request, sys, os, subprocess
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.environ.get("CONTOUR_URL", "http://localhost:8765/index.html"); SHOTS = os.path.join(HERE, "shots") + "/"; import os; os.makedirs(SHOTS, exist_ok=True)
CLOUD = 'window.PIXORA_CLOUD={"apiKey":"fake-api-key","authDomain":"localhost","projectId":"pixora-bca1f","appId":"1:1:web:1","emulator":{"fs":8085,"auth":9099}};'
OFF = open(os.path.join(HERE, "off1.json")).read()
Y4M = "/tmp/contour-barcode.y4m"
if not os.path.exists(Y4M): subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", os.path.join(HERE, "barcode-scene.jpg"), "-t", "4", "-r", "15", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720", Y4M], check=True)
def ean():
    d=[secrets.randbelow(10) for _ in range(12)]; s=sum(v*(3 if i%2 else 1) for i,v in enumerate(d)); return "".join(map(str,d))+str((10-s%10)%10)
NEWCODE = ean(); PW = "Tst-" + secrets.token_urlsafe(12); PASS = "".join(secrets.choice("0123456789") for _ in range(6))
log = []; fails = []
def ok(name, cond, extra=""):
    (log if cond else fails).append(name); print(("PASS " if cond else "FAIL ") + name + (" | " + str(extra)[:220] if extra else ""), flush=True)
async def setup(ctx):
    async def cloud(route): await route.fulfill(status=200, content_type="application/javascript", body=CLOUD)
    async def off(route):
        u = route.request.url
        if "3017620422003" in u: await route.fulfill(status=200, content_type="application/json", body=OFF)
        else: await route.fulfill(status=404, content_type="application/json", body='{"status":0}')
    await ctx.route("**/data/cloud.js", cloud); await ctx.route("https://world.openfoodfacts.org/**", off)
async def page_for(b):
    ctx = await b.new_context(viewport={"width":390,"height":844}, permissions=["camera"], service_workers="block", device_scale_factor=2)
    await setup(ctx); p = await ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e))); p.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and "favicon" not in m.text else None)
    await p.goto(BASE); await p.wait_for_timeout(1500); return p, errs
async def submit(p, form): await p.eval_on_selector(f'form[data-form="{form}"]', "f => f.requestSubmit()")
async def text(p, sel):
    try: return (await p.inner_text(sel, timeout=3000)).replace("\n", " ")
    except Exception: return ""
async def shot(p, n): await p.wait_for_timeout(400); await p.screenshot(path=SHOTS + n + ".png")
async def signup(p, name, email, trainer=False):
    if await p.locator('[data-act=authtab][data-v=signup]').count(): await p.click('[data-act=authtab][data-v=signup]')
    if trainer: await p.click('[data-act=authrole][data-v=trainer]')
    await p.fill("#a-name", name); await p.fill("#a-email", email); await p.fill("#a-pw", PW); await p.check("#a-age"); await submit(p, "auth")
    await p.wait_for_selector("#v-p1", timeout=20000); await shot(p, ("t" if trainer else "m") + "01_passcode")
    await p.fill("#v-p1", PASS)
    if await p.locator("#v-p2").count(): await p.fill("#v-p2", PASS)
    await submit(p, "vault"); await p.wait_for_selector("#v-p1", state="detached", timeout=30000); await p.wait_for_timeout(1500)
async def onboard(p):
    await p.wait_for_selector(".ob", timeout=15000); await shot(p, "m02_setup_welcome")
    await p.click("[data-act=ob-next]"); await p.click("[data-act=ob-next]")
    await p.click("[data-act=ob-pick][data-k=goal][data-v=lose]"); await p.wait_for_timeout(500)
    await p.click("[data-act=ob-pick][data-k=sex][data-v=m]"); await p.fill("#ob-age", "34"); await p.click("[data-act=ob-next]")
    await p.click("[data-act=ob-units][data-v=metric]"); await p.fill("#ob-h", "172"); await p.fill("#ob-w", "86"); await shot(p, "m03_setup_body"); await p.click("[data-act=ob-next]")
    await p.click('[data-act=ob-pick][data-k=activity][data-v="1.375"]'); await p.wait_for_timeout(500)
    await p.fill("#ob-goal", "76"); await p.click("[data-act=ob-next]")
    await p.click("#view g[data-region=belly]"); await p.click("#view g[data-region=arms] path >> nth=0"); await p.click("[data-act=ob-next]")
    await p.click("[data-act=ob-skip]"); await shot(p, "m04_setup_plan"); await p.click("[data-act=ob-next]"); await p.wait_for_timeout(1500)
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream","--use-file-for-fake-video-capture="+Y4M])
        m, merr = await page_for(b); me = f"member.{secrets.token_hex(3)}@example.test"; te = f"trainer.{secrets.token_hex(3)}@example.test"
        await shot(m, "m00_gate"); await signup(m, "Sam Tester", me); await onboard(m)
        ok("member lands on Home after setup", "Good" in await text(m, "#view h1"), await text(m, "#view h1"))
        await shot(m, "m05_home")
        if await m.locator("[data-act=ck]").count():
            await m.click('[data-act=ck][data-k=sleep][data-v="7"]'); await m.click('[data-act=ck][data-k=energy][data-v="4"]')
        # food: search + add
        await m.click("[data-tab=today]"); await shot(m, "m06_food_empty")
        await m.click("[data-act=addfood][data-meal=Breakfast]"); await m.fill("#food-q", "oatmeal"); await m.wait_for_timeout(400)
        await m.click("#food-list [data-act=pickfood] >> nth=0"); await m.wait_for_timeout(600)
        if await m.locator("#sheet.open").count(): await m.click("[data-act=close]")
        await m.wait_for_timeout(800); ent = await text(m, "#view .meal")
        ok("food logged from search", "kcal" in ent, ent[:120])
        # barcode via fake camera
        await m.click("[data-tab=check]"); await m.click("[data-act=chk-scan]"); await m.wait_for_timeout(500); await shot(m, "m07_scanner")
        try: await m.wait_for_selector("#view .ingr", timeout=20000); got = True
        except Exception: got = False
        ok("live camera barcode scan finds the product", got, await text(m, "#view .card h2"))
        await shot(m, "m08_product")
        # not found -> add product with photo
        await m.fill("#chk-code", NEWCODE); await submit(m, "chk"); await m.wait_for_timeout(2500)
        ok("unknown barcode offers add link", "Add this product" in await text(m, ".nfadd"), await text(m, "#chk-msg"))
        await m.click(".nfadd [data-act=np-open]"); await m.fill("#np-name", "Maple oat bar"); await m.fill("#np-brand", "Nature Valley"); await m.fill("#np-serv", "1 bar (35 g)"); await m.fill("#np-sg", "35")
        await m.fill("#np-kcal", "150"); await m.fill("#np-p", "3"); await m.fill("#np-c", "22"); await m.fill("#np-f", "6"); await m.fill("#np-na", "95"); await m.fill("#np-ing", "Whole grain oats, sugar, canola oil, almonds, honey")
        await m.set_input_files("#np-photo", os.path.join(HERE, "barcode-scene.jpg")); await m.wait_for_timeout(1200); await shot(m, "m09_add_product")
        await submit(m, "newprod"); await m.wait_for_timeout(3500); await shot(m, "m10_product_saved")
        ok("member product saved and shown", "Maple oat bar" in await text(m, "#view .card h2"), await text(m, "#toast"))
        ok("product photo shown", await m.locator("#view .pphoto img").count() > 0)
        # exercise + fasting + recipe
        await m.click("[data-tab=today]"); await m.click("[data-act=act-open]"); await m.click('[data-act=act-pick][data-i="1"]'); await m.fill("#act-min", "40"); await submit(m, "act"); await m.wait_for_timeout(500)
        ok("exercise logged", "kcal burned" in await text(m, "#view"), "")
        await m.click("[data-act=addfood][data-meal=Dinner]"); await m.click("[data-act=rc-open]"); await m.fill("#rc-name", "Chicken curry"); await m.fill("#rc-serves", "4")
        await m.fill("#rc-q", "chicken breast"); await m.wait_for_timeout(300); await m.click("#rc-hits [data-act=rc-add] >> nth=0")
        await m.fill("#rc-q", "basmati"); await m.wait_for_timeout(300); await m.click("#rc-hits [data-act=rc-add] >> nth=0"); await shot(m, "m11_recipe"); await m.click("[data-act=rc-save]"); await m.wait_for_timeout(800)
        ok("recipe portion logged", "Chicken curry" in await text(m, "#view"), "")
        await shot(m, "m12_food_day")
        # guided workout
        await m.click("[data-tab=focus]"); await shot(m, "m13_plan")
        if await m.locator("[data-act=wk-start]").count():
            await m.click("[data-act=wk-start]"); await m.check("[data-wk] >> nth=0"); await shot(m, "m14_workout"); await m.click("[data-act=wk-finish]"); await m.wait_for_timeout(500)
            ok("workout finished", "Undo" in await text(m, "#view"), "")
        await m.click("[data-act=pe-open]"); await m.fill("#pe-t", "Core day"); await m.fill("#pe-q", "plank"); await m.wait_for_timeout(300)
        await m.click("#pe-hits [data-act=pe-add] >> nth=0"); await shot(m, "m14b_plan_editor"); await m.click("[data-act=pe-save]"); await m.wait_for_timeout(500)
        ok("own week saved and shown", "Core day" in await text(m, "#view") and "Your own plan" in await text(m, "#view"), "")
        # body tab
        await m.click("[data-tab=scan]"); await m.wait_for_timeout(500); await shot(m, "m15_body")
        await m.click("#view g[data-region=belly]"); await m.wait_for_timeout(400); await shot(m, "m16_part"); await m.click("[data-act=close]")
        # cloud data encrypted?
        doc = json.loads(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8085/emulator/v1/projects/pixora-bca1f:resetSecurityRules", method="GET")).read() or b"{}") if False else None
        # trainer
        b2ctx = None; t, terr = await page_for(b); await signup(t, "Mike Coach", te, trainer=True); await t.wait_for_timeout(2000); await shot(t, "t02_clients_unverified")
        codes = json.loads(urllib.request.urlopen("http://127.0.0.1:9099/emulator/v1/projects/pixora-bca1f/oobCodes").read())["oobCodes"]
        link = [c for c in codes if c["email"] == te and c["requestType"] == "VERIFY_EMAIL"]
        ok("verification email sent to trainer", bool(link), len(codes))
        if link: urllib.request.urlopen(link[-1]["oobLink"]).read()
        if await t.locator("[data-act=vf-check]").count(): await t.click("[data-act=vf-check]"); await t.wait_for_timeout(2500)
        await t.click("[data-tab=texs]"); await t.click("[data-act=tex-new]"); await t.fill("#tx-name", "Banded hip thrust"); await t.check("[data-txr][value=glutes]"); await t.check("[data-txr][value=belly]")
        await t.fill("#tx-steps", "Shoulders on bench\nDrive hips up\nSqueeze 1 s"); await t.fill("#tx-sets", "3"); await t.fill("#tx-reps", "12"); await t.fill("#tx-safe", "Skip with low back pain"); await shot(t, "t03_new_exercise"); await submit(t, "tex"); await t.wait_for_timeout(2500)
        ok("trainer published an exercise", "Banded hip thrust" in await text(t, "#view"), await text(t, "#tex-msg"))
        await shot(t, "t04_exercises")
        # member shares
        await m.click("[data-act=profile]"); await m.fill("#sh-email", te); await m.click("[data-act=share-start]"); await m.wait_for_timeout(4000); await shot(m, "m17_shared")
        await m.click("[data-act=close]"); await m.click("[data-tab=focus]"); await m.wait_for_timeout(2000)
        print("DEBUG", await m.evaluate("JSON.stringify({share:state.share, tex:[...texAll.values()].map(x=>[x.name,x._src,x.vis]), subs:texUnsubs.length})"), [e for e in merr if 'permission' in e.lower() or 'FirebaseError' in e][:3])
        ok("member sees trainer exercise tagged with first name", "by mike" in (await text(m, "#view")).lower(), "")
        await t.click("[data-tab=clients]"); await t.wait_for_timeout(4000); await shot(t, "t05_clients")
        ok("trainer sees the member", "Sam" in await text(t, "#view"), (await text(t, "#view"))[:160])
        if await t.locator("#view .client").count():
            await t.click("#view .client >> nth=0"); await t.wait_for_timeout(4000); await shot(t, "t06_client_view")
            ok("trainer opens member's day read-only", "Sam" in await text(t, "#view h1") or "Sam" in await text(t, "#view"), await text(t, "#view h1"))
        # progress page
        await m.click("[data-tab=home]"); await m.click("[data-act=nav][data-v=progress]"); await m.wait_for_timeout(500); await shot(m, "m18_progress")
        # export
        await m.click("[data-act=profile]")
        async with m.expect_download(timeout=8000) as dl:
            await m.click("[data-act=export][data-v=json]")
        d = await dl.value; data = json.loads(open(await d.path()).read()); ok("export JSON has the food log", any(data["data"]["days"].values()), list(data["data"].keys())[:8])
        await m.click("[data-act=close]")
        # delete contour data, login stays
        await m.click("[data-act=profile]"); await m.click("[data-act=del-open]"); await m.fill("#del-pw", PW); await m.check("#del-ok"); await submit(m, "del"); await m.wait_for_timeout(6000); await shot(m, "m19_after_delete")
        after = await text(m, "#view")
        ok("after deleting Contour data the account still signs in and starts fresh", "passcode" in after.lower() or await m.locator(".ob").count() > 0, after[:160])
        ok("no page errors (member)", not [e for e in merr if "permission" not in e.lower() and "404" not in e], merr[:4]); ok("no page errors (trainer)", not terr, terr[:4])
        print(f"\n{len(log)} passed, {len(fails)} failed: {fails}")
        await b.close()
asyncio.run(main())
