import os
import time
import random
import requests
import urllib.parse
import logging
import sys

# ================= ⚙️ 配置区域 =================
NUM_CARDS = 84
OUTPUT_DIR = ".aidixit/startup"
DELAY_SECONDS = 12
COMPLEXITY_RATIO = 0.4 
LOG_FILE = "dixit_generation.log"

# ================= 📝 日志系统 =================
def setup_logging():
    logger = logging.getLogger("DixitBot")
    logger.setLevel(logging.INFO)
    logger.handlers = [] 
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logging()

# ================= 📚 素材库 =================
SUBJECTS = [
    "a vintage pocket watch", "a lonely wooden ladder", "an open birdcage", 
    "a grand piano", "a steam train", "a lighthouse", "a giant chess piece",
    "a red umbrella", "a spiral staircase", "an antique key", "a glass bottle",
    "a hot air balloon", "a mechanical heart", "a mirror frame", "a suitcase",
    "a typewriter", "a sewing machine", "a gramophone", "an oversized chair",
    "a floating whale", "a fox made of fire", "a deer with branches for antlers",
    "a giant owl reading a book", "a jellyfish made of electric neon", 
    "a snail carrying a house", "a flock of paper cranes", "a cat made of shadows",
    "a fish swimming in the air", "a mechanical butterfly", "a tortoise with a city on its back",
    "a scarecrow in a formal suit", "a tiny astronaut", "a girl holding a lantern",
    "a boy fishing for stars", "a stone statue weeping", "a diver in a forest",
    "a king wearing a crown of thorns", "a ballerina dancing on a needle",
    "a painter painting reality", "a shadow with no owner",
    "a tree made of crystal", "a cloud shaped like a dog", "a giant human eye",
    "a moon melting like cheese", "a sun trapped in a jar", "a giant feather",
    "a mushroom house", "a tornado of letters", "a lightning bolt frozen in ice",
    "an apple floating in zero gravity", "a rose growing from concrete"
]

ACTIONS = [
    "melting into colorful liquid", "shattering into glass fragments",
    "evaporating into smoke", "unraveling like a ball of yarn",
    "exploding into a flock of butterflies", "turning into sand",
    "crystallizing into ice", "burning with cold blue flames",
    "floating upside down", "leaking galaxies instead of water",
    "growing giant roots into the sky", "being sewn together with red thread",
    "bleeding paint colors", "glowing from the inside out",
    "casting a shadow that is alive", "freezing time around it",
    "playing silent music", "sleeping eternally in a bubble",
    "eating the clouds", "opening a zipper to another dimension",
    "dripping numbers and letters"
]

LOCATIONS = [
    "in the middle of a dry desert at night", "deep underwater in a coral reef",
    "in a dense forest of giant mushrooms", "on a snowy mountain peak",
    "inside a cave filled with glowing crystals", "on a beach made of glass",
    "in a field of sunflowers facing the wrong way",
    "on top of a fluffy cloud city", "floating in deep outer space",
    "on a chessboard landscape", "inside a giant teacup",
    "walking on a tightrope between stars", "on an island floating in the sky",
    "inside a maze of mirrors", "on a bridge that ends abruptly",
    "in a world made entirely of paper", "inside an hourglass",
    "on a staircase to nowhere", "in a room with no gravity",
    "inside an old dusty library", "in a flooded ballroom",
    "inside the mechanism of a giant clock", "in an abandoned theater",
    "inside a bottle drifting at sea", "in a greenhouse of metal flowers"
]

RELATIONS = [
    "In the foreground, [A], while far away in the background, [B]",
    "On the left side, [A], facing [B] on the right side",
    "High above, [A] is looming over a tiny [B] below",
    "[A] is floating directly above [B]",
    "[A] is looking into a mirror, but the reflection shows [B]",
    "The shadow of [A] is shaped exactly like [B]",
    "[A] is slowly transforming into [B]",
    "[A] is breaking apart, and [B] is coming out from inside it",
    "[A] is holding a string attached to a floating [B]",
    "[A] is painting a picture of [B] on a canvas",
    "[A] is trying to catch [B] with a net",
    "[A] is opening a door that leads to [B]",
    "[A] is trapped inside a glass jar held by [B]",
    "[A] is dreaming, and the dream cloud shows [B]",
    "A trail of footprints leads from [A] to [B]",
    "[A] and [B] are dancing together in the air"
]

MOODS = [
    "whimsical", "melancholic", "eerie", "peaceful", "cyberpunk", 
    "vintage", "gothic", "dreamy", "surreal", "romantic", "mysterious", "playful"
]

# ================= 🛠️ 核心逻辑 =================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def clean_text(text):
    return text.replace("**", "").replace('"', '').strip()

def construct_concept(index):
    """构建概念并获取 AI 描述 (修复了变量作用域bug + 增加了文本重试)"""
    is_complex = random.random() < COMPLEXITY_RATIO
    mood = random.choice(MOODS)
    location = random.choice(LOCATIONS)
    
    instruction = ""
    log_prefix = f"[{index+1}/{NUM_CARDS}]"
    
    # 提前准备好兜底 Prompt 变量，防止后面报错
    fallback_prompt = ""

    if is_complex:
        subj_1, subj_2 = random.sample(SUBJECTS, 2)
        act_1 = random.choice(ACTIONS)
        act_2 = random.choice(ACTIONS)
        relation_template = random.choice(RELATIONS)
        
        phrase_1 = f"{subj_1} that is {act_1}"
        phrase_2 = f"{subj_2} that is {act_2}"
        spatial_desc = relation_template.replace("[A]", phrase_1).replace("[B]", phrase_2)
        
        logger.info(f"🤖 {log_prefix} 构思: 双重叙事 ({mood})")
        logger.info(f"   -> 骨架: {spatial_desc} @ {location}")
        
        instruction = (
            f"Generate a surreal Dixit card description. "
            f"Setting: {location}. Mood: {mood}. "
            f"Composition/Story: {spatial_desc}. "
            "Describe the visual contrast and connection between the two elements. "
            "Make it artistic, abstract, and poetic. "
            "Output ONLY the description."
        )
        # 修复点 1：在这里正确定义复杂模式下的兜底词
        fallback_prompt = f"Surreal art of {spatial_desc}, set in {location}, {mood} style"
        
    else:
        subj = random.choice(SUBJECTS)
        act = random.choice(ACTIONS)
        
        logger.info(f"🤖 {log_prefix} 构思: 经典聚焦 ({mood})")
        logger.info(f"   -> 骨架: {subj} + {act} @ {location}")
        
        instruction = (
            f"Generate a surreal Dixit card description. "
            f"Subject: {subj}. Action: {act}. Setting: {location}. Mood: {mood}. "
            "Focus on the fine details, texture, and the surreal atmosphere. "
            "Output ONLY the description."
        )
        # 修复点 1：在这里正确定义简单模式下的兜底词
        fallback_prompt = f"Surreal art of {subj} {act}, set in {location}, {mood} style"

    # 请求 Text API (修复点 2：增加重试循环)
    prompt_encoded = urllib.parse.quote(instruction)
    seed = random.randint(0, 100000)
    url = f"https://text.pollinations.ai/{prompt_encoded}?seed={seed}&model=openai"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                desc = clean_text(response.text)
                elapsed = time.time() - start_time
                logger.info(f"   💡 获得灵感 (耗时 {elapsed:.2f}s): {desc[:60]}...")
                return desc
            else:
                logger.warning(f"   ⚠️ 文本API状态码 {response.status_code}，重试中 ({attempt+1}/{max_retries})...")
                time.sleep(2)
                
        except Exception as e:
            logger.warning(f"   ⚠️ 获取灵感网络异常: {e}，重试中 ({attempt+1}/{max_retries})...")
            time.sleep(2)
    
    # 如果重试 3 次都失败，使用我们提前准备好的 fallback_prompt
    logger.error(f"   ❌ 多次尝试失败，启用兜底 Prompt")
    return fallback_prompt

def generate_image(prompt, filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    full_prompt = f"{prompt}, surreal masterpiece, Dixit board game style, vector art, soft colors, 8k resolution, highly detailed"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = random.randint(0, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}&width=1024&height=1024"
    
    headers = {"User-Agent": "Mozilla/5.0"}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"   🎨 正在绘制 (尝试 {attempt+1}/{max_retries})...")
            start_t = time.time()
            
            r = requests.get(url, headers=headers, timeout=120)
            
            if r.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                elapsed = time.time() - start_t
                file_size = os.path.getsize(file_path) / 1024 
                logger.info(f"   ✅ 保存成功: {filename} ({file_size:.1f}KB, 耗时 {elapsed:.1f}s)")
                return True
            else:
                logger.warning(f"   ⚠️ 图片服务器错误: {r.status_code}，等待重试...")
                time.sleep(5)
                
        except requests.exceptions.ReadTimeout:
            logger.warning(f"   🐢 生成超时 (服务器繁忙)，等待重试...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"   ❌ 连接异常: {e}")
            time.sleep(5)
            
    logger.error(f"   ❌ {filename} 最终失败，跳过。")
    return False

# ================= 🚀 主程序 =================

def main():
    ensure_dir(OUTPUT_DIR)
    logger.info("=========================================")
    logger.info(f"   《画物语》终极生成器 (修复版)")
    logger.info(f"   目标: {NUM_CARDS} 张 | 输出: {OUTPUT_DIR}")
    logger.info(f"   日志文件: {LOG_FILE}")
    logger.info("=========================================\n")
    
    total_start = time.time()
    
    try:
        for i in range(NUM_CARDS):
            filename = f"card_{i+1:02d}.jpg"
            file_path = os.path.join(OUTPUT_DIR, filename)
            
            # 断点续传检查
            if os.path.exists(file_path):
                logger.info(f"⏭️  [{i+1}/{NUM_CARDS}] 跳过: {filename} 已存在")
                continue
            
            # 1. 构思
            prompt = construct_concept(i)
            
            # 2. 绘图
            success = generate_image(prompt, filename)
            
            # 3. 冷却
            if success:
                if i < NUM_CARDS - 1:
                    wait = DELAY_SECONDS + random.randint(2, 6)
                    logger.info(f"   ⏳ 冷却中... ({wait}s)\n")
                    time.sleep(wait)
            else:
                logger.warning(f"   ⚠️ 本次生成失败，休息 5s 后继续\n")
                time.sleep(5)
                
    except KeyboardInterrupt:
        logger.warning("\n🛑 用户手动停止脚本")
    except Exception as e:
        logger.critical(f"\n☠️ 发生未捕获的异常: {e}")
    finally:
        total_time = (time.time() - total_start) / 60
        logger.info("=========================================")
        logger.info(f"🎉 任务结束！总耗时: {total_time:.1f} 分钟")
        logger.info(f"📂 查看图片: {os.path.abspath(OUTPUT_DIR)}")
        logger.info(f"📝 查看详细日志: {os.path.abspath(LOG_FILE)}")
        logger.info("=========================================")

if __name__ == "__main__":
    main()