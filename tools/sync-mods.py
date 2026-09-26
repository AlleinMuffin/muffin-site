#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 GitHub 整合包仓库的 mods/ 目录拉取真实模组清单，生成 src/data/mods.ts。

用法：
    python tools/sync-mods.py                    # 用默认仓库与分支
    python tools/sync-mods.py --repo 用户/仓库 --branch main

生成的文件会被 git 跟踪（构建时直接读，不需要联网）。
仓库地址改了就改下面的 DEFAULT_REPO，或命令行传 --repo。
"""
import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_REPO = "AlleinMuffin/Muffin-s-ModPack-Mod-Updated"
DEFAULT_BRANCH = "main"
MODS_DIR = "mods"

OUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "data", "mods.ts",
)

# ---------------------------------------------------------------- 名称覆盖表
# 文件名解析不出来、或解析得难看的，在这里人工指定：文件名 -> (显示名, 版本)
OVERRIDES = {
    "abbm-禁止转载-Do-Not-Redistribute-1.1.0.jar": ("ABBM", "1.1.0"),
    "Epic Villages 1.3.0 (1.21+).jar": ("Epic Villages", "1.3.0"),
    "MaidUseHandCrank_1.6.2-neoforge_21.1.219-1.21.1.jar": ("Maid Use Hand Crank", "1.6.2"),
    "DistantHorizons-3.0.3-b-1.21.1-fabric-neoforge.jar": ("Distant Horizons", "3.0.3-b"),
    "create_aeronautics_toolgun-0.2.2.jar": ("Create Aeronautics Toolgun", "0.2.2"),
    "c2me-neoforge-mc1.21.1-0.4.0-alpha.0.113.jar": ("C2ME", "0.4.0-alpha.113"),
    "fastleafdecay-35.jar": ("Fast Leaf Decay", "35"),
    "netmusic-1.5.1-neoforge+mc1.21.1.jar": ("Net Music", "1.5.1"),
    "wwoo-2.3.4.jar": ("WWOO", "2.3.4"),
    "smsn-neoforge-1.4.1-1.21.1.jar": ("SMSN", "1.4.1"),
    "smrb-1.0.0.jar": ("SMRB", "1.0.0"),
    "sync-mods-placeholder": ("", ""),
}

# 已知模组的规范显示名（只影响显示，不影响版本解析）
PRETTY = {
    "create": "Create", "jei": "JEI", "jade": "Jade", "sodium": "Sodium",
    "lithium": "Lithium", "iris": "Iris", "spark": "Spark", "chunky": "Chunky",
    "curios": "Curios API", "geckolib": "GeckoLib", "kubejs": "KubeJS",
    "rhino": "Rhino", "patchouli": "Patchouli", "balm": "Balm",
    "bookshelf": "Bookshelf", "placebo": "Placebo", "architectury": "Architectury API",
    "cloth-config": "Cloth Config", "configured": "Configured",
    "ferritecore": "FerriteCore", "modernfix": "ModernFix",
    "immediatelyfast": "ImmediatelyFast", "krypton_fnp": "Krypton",
    "kotlinforforge": "Kotlin for Forge", "veil": "Veil",
    "farmersdelight": "Farmer's Delight", "brewinandchewin": "Brewin' And Chewin",
    "mynethersdelight": "My Nether's Delight", "ends_delight": "End's Delight",
    "appleskin": "AppleSkin", "carryon": "Carry On", "controlling": "Controlling",
    "mousetweaks": "Mouse Tweaks", "jecharacters": "Just Enough Characters",
    "xaerominimap": "Xaero's Minimap", "xaeroworldmap": "Xaero's World Map",
    "naturescompass": "Nature's Compass", "structurecompass": "Structure Compass",
    "touhoulittlemaid": "Touhou Little Maid", "maidsoulkitchen": "Maid Soul Kitchen",
    "immersiveengineering": "Immersive Engineering",
    "immersivepetroleum": "Immersive Petroleum",
    "immersive_aircraft": "Immersive Aircraft",
    "cc-tweaked": "CC: Tweaked", "cc_sable": "CC: Sable", "cc-sable": "CC: Sable",
    "sable": "Sable", "alwayseat": "Always Eat", "bits-n-bobs": "Bits 'n' Bobs",
    "constructionwand-kots": "Construction Wand",
    "enchdesc": "Enchantment Descriptions",
    "naturescompass": "Nature's Compass",
    "usefulslime": "Useful Slime", "nochatreports": "No Chat Reports",
    "simplebackups": "Simple Backups", "enchdesc": "Enchantment Descriptions",
    "ftb-library": "FTB Library", "ftb-quests": "FTB Quests",
    "ftb-teams": "FTB Teams", "ftb-ultimine": "FTB Ultimine",
    "ftb-xmod-compat": "FTB XMod Compat",
    "forgified-fabric-api": "Forgified Fabric API",
    "yet_another_config_lib_v3": "YetAnotherConfigLib",
    "resourcefullib": "Resourceful Lib",
    "resourcefulconfig": "Resourceful Config",
    "ldlib2": "LDlib", "l2library": "L2 Library",
    "lootr": "Lootr", "lootjs": "LootJS",
    "exposure": "Exposure", "torchmaster": "Torchmaster",
    "modulargolems": "Modular Golems", "irons_jewelry": "Iron's Jewelry",
    "do_a_barrel_roll": "Do a Barrel Roll",
    "simpletomb": "Simple Tomb", "simpletomb": "Simple Tomb",
    "prickle": "Prickle", "polymorph": "Polymorph",
    "connector": "Connector", "frequency": "Frequency",
    "aeroworks": "AeroWorks", "deployer": "Deployer",
    "drivebywire": "Drive By Wire", "escalated": "Escalated",
    "fxntstorage": "FXNT Storage", "fluidlogistics": "Fluid Logistics",
    "flerovium": "Flerovium", "alloy_smelter": "Alloy Smelter",
    "electroenergetics": "Electro Energetics",
    "synaxis": "Synaxis", "tradeworks": "Trade Works",
    "trading_floor": "Trading Floor",
    "mechanicals": "Mechanicals", "horseman": "Horseman",
    "hotbath": "Hot Bath", "abbm": "ABBM",
    "usefulslime": "Useful Slime",
    "simplebackups": "Simple Backups",
    "nochatreports": "No Chat Reports",
    "attributefix": "AttributeFix",
    "maxhealthfix": "Max Health Fix",
    "imblocker": "IMBlocker",
    "disconnect-packet-fix": "Disconnect Packet Fix",
    "packetfixer": "Packet Fixer",
    "fasttag": "Fast Tag", "fastrecipesearch": "Fast Recipe Search",
    "efficient_hashing": "Efficient Hashing",
    "zfastnoise": "ZFastNoise",
    "framework": "Framework", "fzzy_config": "Fzzy Config",
    "atlas_api": "Atlas API", "sable-schematic-api": "Sable Schematic API",
    "colorfulhearts": "Colorful Hearts",
    "colorwheel": "ColorWheel", "colorwheel_patcher": "ColorWheel Patcher",
    "copycats": "Copycats+", "railways": "Create: Steam 'n' Rails",
    "createdeco": "Create: Deco",
    "createdieselgenerators": "Create: Diesel Generators",
    "createaddition": "Create Crafts & Additions",
    "createbigcannons": "Create: Big Cannons",
    "createoreexcavation": "Create Ore Excavation",
    "create_new_age": "Create: New Age",
    "create_connected": "Create: Connected",
    "create_easy_structures": "Create Easy Structures",
    "create_hypertube": "Create: Hypertube",
    "create_compressed": "Create Compressed",
    "create-integrated-farming": "Create Integrated Farming",
    "create-central-kitchen": "Create: Central Kitchen",
    "create-enchantment-industry": "Create: Enchantment Industry",
    "create_mechanical_spawner": "Create Mechanical Spawner",
    "create_pattern_schematics": "Create Pattern Schematics",
    "create_power_loader": "Create Power Loader",
    "create_tweaked_controllers": "Create Tweaked Controllers",
    "createultimine": "Create Ultimine",
    "createprism": "Create Prism",
    "createpropulsion": "Create Propulsion",
    "createrailgrinding": "Create Rail Grinding",
    "createredstonelinkgui": "Create Redstone Link GUI",
    "createliquidfuel": "Create Liquid Fuel",
    "creategearsandtavern": "Create Gears & Tavern",
    "createbetterfps": "Create Better FPS",
    "createadditionallogistics": "Create Additional Logistics",
    "createdragonsplus": "Create Dragons Plus",
    "createfastschematiccannon": "Create Fast Schematic Cannon",
    "c6c-lite": "C6C Lite",
    "cmpackagecouriers": "CM Package Couriers",
    "clientsort": "Client Sort",
    "kaleidoscopecookery": "Kaleidoscope Cookery",
    "kaleidoscopedoll": "Kaleidoscope Doll",
    "kaleidoscopetavern": "Kaleidoscope Tavern",
    "kaleidoscope_compat": "Kaleidoscope Compat",
    "barbequesdelight": "Barbecue's Delight",
    "chefsdelight": "Chef's Delight",
    "displaydelight": "Display Delight",
    "cratedelight": "Crate Delight",
    "vanillin": "Vanillin",
    "byepregen": "Bye Pregen",
    "biomespy": "Biome Spy",
    "takesapillage": "Takes A Pillage",
    "hopobetterruinedportals": "Hopo Better Ruined Portals",
    "medieval_buildings_end_edition": "Medieval Buildings: End Edition",
    "structure_layout_optimizer": "Structure Layout Optimizer",
    "smart_bounds": "Smart Bounds",
    "simulated_gauges": "Simulated Gauges",
    "extra_gauges": "Extra Gauges",
    "ritchiesprojectilelib": "Ritchie's Projectile Lib",
    "powerful_dummy": "Powerful Dummy",
    "showcaseitem": "Showcase Item",
    "display_case": "Display Case",
    "sootychimneys": "Sooty Chimneys",
    "tracks": "Tracks",
    "flatbedrock": "Flat Bedrock",
    "always_eat": "Always Eat",
    "retraining": "Retraining",
    "searchables": "Searchables",
    "justenoughprofessions": "Just Enough Professions",
    "particular": "Particular",
    "betteradvancements": "Better Advancements",
    "configureddefaults": "Configured Defaults",
    "jadeaddons": "Jade Addons",
    "apothicattributes": "Apothic Attributes",
    "betteradvancements": "Better Advancements",
    "chunky": "Chunky",
    "controlling": "Controlling",
    "curios": "Curios API",
    "serverwarashi": "Server Warashi",
    "takeapillage": "Takes A Pillage",
    "reddensstonelantern": "Redden's Stone Lantern",
    "lmft": "LMFT",
}

# 需要丢弃的 token：加载器、平台、打包标记
DROP_TOKENS = {
    "neoforge", "neoforged", "forge", "fabric", "quilt", "neo",
    "all", "full", "bundled", "merged", "local", "server", "client",
    "hotfix", "build", "beta", "alpha", "release", "mc", "api",
    "jar", "mod", "final", "snapshot",
}
# Minecraft 版本号白名单：只有这些才当作 MC 版本丢掉。
# 不能写成「凡 1.x 就丢」——很多模组自己就叫 1.0.0 / 1.2.6，会被误杀。
MC_SET = {
    "1.20", "1.20.1", "1.20.4", "1.20.5", "1.20.6",
    "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4", "1.21.5",
    "1.21.6", "1.21.7", "1.21.8", "1.21.9",
}
# 「这一位开始是版本号」的判定：数字开头，或 v 开头紧跟数字（v21.1.3）
VERSION_START = re.compile(r"^v?\d")


def is_mc_version(token):
    t = token.lower()
    if t.startswith("mc"):
        t = t[2:]
    return t in MC_SET

# ------------------------------------------------------------------ 分类规则
# 按顺序匹配，命中即返回（越靠前优先级越高）
CATEGORY_RULES = [
    ("Create 生态", ["create", "copycats", "railways", "c6c", "deployer",
                     "drivebywire", "escalated", "flerovium",
                     "alloy_smelter", "fluidlogistics", "electroenergetics",
                     "extra_gauges", "simulated_gauges", "mechanicals",
                     "synaxis", "tracks"]),
    ("科技与自动化", ["cc-tweaked", "cc_sable", "sable", "frequency",
                      "aeroworks", "kubejs", "lootjs", "rhino"]),
    ("工业能源", ["immersive", "createaddition", "creatediesel", "new_age",
                  "createliquidfuel", "createoreexcavation", "createpropulsion",
                  "createprism", "createbigcannons", "fxntstorage",
                  "createultimine", "createrailgrinding"]),
    ("食物烹饪", ["delight", "brewin", "vanillin", "barbeques", "chefs",
                  "cratedelight", "displaydelight", "maidsoulkitchen",
                  "hotbath", "creativecentral", "central-kitchen", "farmers"]),
    ("性能优化", ["sodium", "lithium", "ferritecore", "immediatelyfast",
                  "modernfix", "c2me", "krypton", "efficient_hashing",
                  "fasttag", "fastrecipesearch", "byepregen", "chunky",
                  "smart_bounds", "createbetterfps", "spark", "zfastnoise",
                  "structure_layout_optimizer", "flatbedrock", "fastleafdecay"]),
    ("客户端 UI", ["jade", "jei", "xaero", "iris", "appleskin", "controlling",
                   "mousetweaks", "colorfulhearts", "betteradvancements",
                   "searchables", "clientsort", "cloth", "yet_another_config",
                   "resourcefulconfig", "exposure", "particular",
                   "showcaseitem", "display_case", "simpletomb",
                   "justenoughprofessions", "configured", "configureddefaults",
                   "fzzy_config", "jecharacters", "redstonelinkgui"]),
    ("世界与建筑", ["epic villages", "biomespy", "medieval", "takesapillage",
                    "ruinedportals", "distant", "naturescompass",
                    "structurecompass", "torchmaster", "lootr", "wwoo",
                    "trading_floor", "tradeworks", "netmusic",
                    "kaleidoscope", "reddensstonelantern", "sootychimneys"]),
    ("工具与实用", ["simplebackups", "nochatreports", "constructionwand",
                    "polymorph", "enchdesc", "retraining", "serverwarashi",
                    "usefulslime", "cmpackagecouriers", "apothic",
                    "colorwheel", "always", "bits_n_bobs"]),
    ("冒险玩法", ["irons_jewelry", "modulargolems", "immersive_aircraft",
                  "do_a_barrel_roll", "touhou", "maid", "horseman",
                  "powerful_dummy", "lootjs", "ftb-quests", "curios",
                  "carryon", "simpletomb", "hotbath"]),
    ("库与依赖", ["architectury", "balm", "bookshelf", "placebo", "patchouli",
                  "kotlinforforge", "rhino", "kubejs", "framework", "geckolib",
                  "l2library", "ldlib", "resourcefullib", "ftb-library",
                  "ftb-teams", "ftb-xmod", "forgified-fabric-api", "connector",
                  "veil", "atlas_api", "prickle", "packetfixer",
                  "disconnect-packet-fix", "attributefix", "maxhealthfix",
                  "imblocker", "lmft", "ldlib2", "config"]),
]


def humanize(tokens):
    """把 token 列表拼成可读名称。"""
    # 先按完整组合匹配（cc + tweaked -> cc-tweaked），再逐词匹配
    joined = "-".join(t.lower() for t in tokens)
    if joined in PRETTY:
        return PRETTY[joined]
    words = []
    for t in tokens:
        low = t.lower()
        if low in PRETTY:
            words.append(PRETTY[low])
        else:
            words.append(t[:1].upper() + t[1:] if t else t)
    return " ".join(words).replace("  ", " ").strip()


def categorize(fname):
    low = fname.lower()
    for cat, keys in CATEGORY_RULES:
        for k in keys:
            if k in low:
                return cat
    return "其他"


def parse(fname):
    """文件名 -> (显示名, 版本)"""
    if fname in OVERRIDES:
        return OVERRIDES[fname]

    stem = fname[:-4] if fname.lower().endswith(".jar") else fname
    stem = re.sub(r"\([^)]*\)", " ", stem).strip()       # 去掉 (1.21+) 之类
    tokens = [t for t in re.split(r"[-_+\s]+", stem) if t]

    name_tokens = []
    rest = []
    hit_version = False
    for t in tokens:
        if hit_version or VERSION_START.match(t) or t.lower() in DROP_TOKENS:
            hit_version = True
            rest.append(t)
        else:
            name_tokens.append(t)

    # 版本段：丢掉加载器标记与 MC 版本号，剩下的才是模组版本
    ver_tokens = []
    for t in rest:
        low = t.lower()
        if low in DROP_TOKENS or is_mc_version(t):
            continue
        ver_tokens.append(t)
    version = "-".join(ver_tokens) or "-"

    name = humanize(name_tokens) or humanize([stem])
    return name, version


def fetch(repo, branch):
    url = f"https://api.github.com/repos/{repo}/contents/{MODS_DIR}?ref={branch}"
    for attempt in range(4):
        try:
            out = subprocess.run(
                ["curl", "-s", "-m", "60", url],
                capture_output=True, timeout=90,
            )
            data = json.loads(out.stdout.decode("utf-8"))
            if isinstance(data, list):
                return data
            sys.stderr.write(f"  第 {attempt+1} 次返回异常: {str(data)[:120]}\n")
        except Exception as e:
            sys.stderr.write(f"  第 {attempt+1} 次失败: {e}\n")
    raise SystemExit("拉取失败：请检查网络或仓库地址")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--branch", default=DEFAULT_BRANCH)
    args = ap.parse_args()

    print(f"拉取 {args.repo}@{args.branch} 的 {MODS_DIR}/ ...")
    entries = fetch(args.repo, args.branch)

    jars = [e for e in entries if e["name"].lower().endswith(".jar")]
    jars.sort(key=lambda e: e["name"].lower())
    print(f"  共 {len(jars)} 个 jar（目录内另有 {len(entries)-len(jars)} 个非 jar 文件）")

    items = []
    for e in jars:
        name, version = parse(e["name"])
        items.append({
            "name": name,
            "version": version,
            "category": categorize(e["name"]),
            "file": e["name"],
            "size": round(e.get("size", 0) / 1024),
        })

    cats = []
    for it in items:
        if it["category"] not in cats:
            cats.append(it["category"])
    cats.sort(key=lambda c: -sum(1 for i in items if i["category"] == c))

    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = [
        "/**",
        " * 模组清单 —— 由 tools/sync-mods.py 从整合包仓库自动生成，不要手改。",
        f" * 来源：{args.repo}@{args.branch} 的 {MODS_DIR}/",
        " * 更新方法：python tools/sync-mods.py",
        " */",
        "",
        "export interface ModItem {",
        "  name: string;",
        "  version: string;",
        "  category: string;",
        "  /** 仓库里的原始文件名，用于核对 */",
        "  file: string;",
        "  /** 文件大小（KB） */",
        "  size: number;",
        "}",
        "",
        "export const mods: ModItem[] = [",
    ]
    for it in items:
        lines.append(
            '  { name: "%s", version: "%s", category: "%s", file: "%s", size: %d },'
            % (esc(it["name"]), esc(it["version"]), esc(it["category"]),
               esc(it["file"]), it["size"])
        )
    lines.append("];")
    lines.append("")
    lines.append("/** 分类按包含模组数量从多到少排序 */")
    lines.append("export const modCategories: string[] = [")
    for c in cats:
        lines.append('  "%s",' % esc(c))
    lines.append("];")
    lines.append("")
    lines.append("/** 模组总数（页面与终端示例都从这里取，避免写死） */")
    lines.append("export const modCount = mods.length;")
    lines.append("")

    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(f"\n已生成 {OUT_FILE}")
    print(f"  模组 {len(items)} 个，分类 {len(cats)} 个")
    for c in cats:
        n = sum(1 for i in items if i["category"] == c)
        print(f"    {c:<10} {n}")


if __name__ == "__main__":
    main()
