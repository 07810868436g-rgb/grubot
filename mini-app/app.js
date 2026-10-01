        // ==========================================
        // ЛОГИКА SPLASH SCREEN (3D-Орбита 4.5 сек)
        // ==========================================
        window.addEventListener('DOMContentLoaded', () => {
            const splash = document.getElementById('splashScreen');
            const eye = document.getElementById('splashEye');
            const title = document.getElementById('splashTitle');
            const loader = document.getElementById('splashLoader');

            setTimeout(() => { eye.classList.add('targeting'); }, 3500);

            setTimeout(() => {
                const rect = eye.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                
                for(let i = 0; i < 60; i++) {
                    let spark = document.createElement('div');
                    spark.className = 'spark';
                    spark.style.left = x + 'px'; spark.style.top = y + 'px';
                    spark.style.setProperty('--dx', (Math.random() * 600 - 300) + 'px');
                    spark.style.setProperty('--dy', (Math.random() * 600 - 300) + 'px');
                    spark.style.animationDuration = (0.4 + Math.random() * 0.4) + 's';
                    splash.appendChild(spark);
                }
                
                eye.style.opacity = '0';
                title.style.opacity = '0';
                loader.style.opacity = '0';
                splash.style.backgroundColor = 'rgba(0,0,0,0)';
                
                setTimeout(() => splash.remove(), 600);
            }, 4000);
        });

        // ==========================================
        // БАЗОВАЯ ИНИЦИАЛИЗАЦИЯ
        // ==========================================
        let tg = window.Telegram.WebApp;
        tg.expand();
        
        const BACKEND_URL = "https://grutap-backend.onrender.com/api"; 
        
        const TRANSLATIONS = {
            ru: {
                navGame: "Игра", navBusiness: "Бизнес", navAirdrop: "Airdrop", navTop: "Топ",
                rocketActive: "🚀 РАКЕТА АКТИВНА! (x5 к тапу)", offlineTitle: "Студия работала!",
                offlineDesc: "Пока вас не было, бот собрал пассивный доход:", claim: "Круто! Забрать",
                currentEffect: "Текущий эффект:", nextEffect: "Следующий:", squadTitle: "Создать официальный Сквад",
                squadRules: "Чтобы ваш канал попал в Лидерборд, добавьте бота @grutap_robot в администраторы вашего канала.",
                squadBind: "Привязать канал", squadYourLink: "Ваша официальная ссылка:", copy: "📋 Скопировать",
                shopTitle: "🛋 Магазин комнат", squadLabel: "Сквад:", levelLabel: "Уровень",
                upgradeStudio: "🛋 Обустроить студию", dailyRewardTitle: "📆 Ежедневная Награда",
                dailyStreak: "Серия входов:", days: "дней", techBoosts: "Технические Бусты",
                multitap: "Мультитап", energy: "Энергия", autobot: "Авто-Бот", rocketTitle: "🚀 Сверхзвуковая Ракета",
                rocketAvailable: "Доступно:", launchRocket: "Запустить Ракету 🚀", friends: "Друзей:",
                withdrawBtn: "🔒 Вывести токены (Скоро)", support: "💬 Связь с менеджером", tasksTitle: "Задания",
                dailyGoalTitle: "🎯 Цель: 5000 тапов", progress: "Прогресс:",
                claimGoal: "Выполни цель 🎯", subscribe: "Подписаться", tenFriends: "10 друзей",
                inviteLink: "Пригласить", topTitle: "🏆 Лидерборд", balance: "Баланс:",
                tabPlayers: "👤 Игроки", tabSquads: "📢 Сквады", yourLeague: "Ваша лига:", topSquadBtn: "🔥 Вывести свой канал в ТОП",
                leagueRank: "Рейтинг:", artifactsTitle: "🏆 Telegram Артефакты", artifactsDesc: "Экипируйте мемы для глобального буста.",
                stakingTitle: "🏦 Web3 Инвестиции", stakingDesc: "Заморозь монеты на 14 дней и получи +40%.", stakeBtn: "Инвестировать (Скоро)",
                pvpTitle: "⚔️ Арена Дуэлей", pvpDesc: "Победитель забирает банк (комиссия сети 5%).", findOpponent: "Найти противника 🔍",
                businessSubtitle: "Инвестируйте в свое развитие", catRealEstate: "🏢 Недвижимость", catRealEstateDesc: "Пассивный доход и прокачка ваших студий",
                catTech: "⚙️ Технологии", catTechDesc: "Мультитап, Энергия, Авто-Бот", catCustom: "💎 Кастомизация", catCustomDesc: "Telegram мемы, Стили Арены, Флекс",
                arenaStylesTitle: "⚔️ Стили Арены (PvP)", profileTitle: "Web3 Паспорт", playerId: "Игрок", connectWallet: "Connect Wallet (Скоро)",
                settingsTitle: "Настройки", languageLabel: "Язык", themeLabel: "Тема Platinum", statsTitle: "Статистика"
            },
            en: {
                navGame: "Game", navBusiness: "Business", navAirdrop: "Airdrop", navTop: "Top",
                rocketActive: "🚀 ROCKET ACTIVE! (x5 per tap)", offlineTitle: "Studio was working!",
                offlineDesc: "While you were away, your bot generated:", claim: "Awesome! Claim",
                currentEffect: "Current effect:", nextEffect: "Next:", squadTitle: "Create Official Squad",
                squadRules: "To get into the Leaderboard, add @grutap_robot as an admin to your channel.",
                squadBind: "Link Channel", squadYourLink: "Your official link:", copy: "📋 Copy Link",
                shopTitle: "🛋 Studio Store", squadLabel: "Squad:", levelLabel: "Level",
                upgradeStudio: "🛋 Upgrade Studio", dailyRewardTitle: "📆 Daily Reward",
                dailyStreak: "Daily streak:", days: "days", techBoosts: "Tech Boosts",
                multitap: "Multitap", energy: "Energy", autobot: "Auto-Bot", rocketTitle: "🚀 Supersonic Rocket",
                rocketAvailable: "Available:", launchRocket: "Launch Rocket 🚀", friends: "Friends:",
                withdrawBtn: "🔒 Withdraw Tokens (Soon)", support: "💬 Contact Support", tasksTitle: "Tasks",
                dailyGoalTitle: "🎯 Goal: 5000 taps", progress: "Progress:",
                claimGoal: "Complete Goal 🎯", subscribe: "Subscribe", tenFriends: "10 Friends",
                inviteLink: "Invite", topTitle: "🏆 Leaderboard", balance: "Balance:",
                tabPlayers: "👤 Players", tabSquads: "📢 Squads", yourLeague: "Your League:", topSquadBtn: "🔥 Promote Channel to TOP",
                leagueRank: "Rank:", artifactsTitle: "🏆 Telegram Artifacts", artifactsDesc: "Equip memes for global boosts.",
                stakingTitle: "🏦 Web3 Investments", stakingDesc: "Stake tokens for 14 days and get +40%.", stakeBtn: "Stake (Soon)",
                pvpTitle: "⚔️ Duel Arena", pvpDesc: "Winner takes the bank (5% network fee).", findOpponent: "Find Opponent 🔍",
                businessSubtitle: "Invest in your progress", catRealEstate: "🏢 Real Estate", catRealEstateDesc: "Passive income and studio upgrades",
                catTech: "⚙️ Technologies", catTechDesc: "Multitap, Energy, Auto-Bot", catCustom: "💎 Customization", catCustomDesc: "Telegram memes, Arena Styles, Flex",
                arenaStylesTitle: "⚔️ Arena Styles (PvP)", profileTitle: "Web3 Passport", playerId: "Player", connectWallet: "Connect Wallet (Soon)",
                settingsTitle: "Settings", languageLabel: "Language", themeLabel: "Platinum Theme", statsTitle: "Statistics"
            }
        };

        const urlParams = new URLSearchParams(window.location.search);
        let currentLang = urlParams.get('lang') || (tg.initDataUnsafe?.user?.language_code === 'en' ? 'en' : 'ru');

        function setLanguage(lang) {
            currentLang = lang;
            document.getElementById('currentLangLabel').innerText = lang.toUpperCase();
            const dict = TRANSLATIONS[lang] || TRANSLATIONS.ru;
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (dict[key]) el.innerText = dict[key];
            });
            renderArtifacts(); 
            renderArenaStyles(); 
        }

        function toggleLanguage() {
            setLanguage(currentLang === 'ru' ? 'en' : 'ru');
            tg.HapticFeedback.selectionChanged();
        }

        function openProfile() {
            document.getElementById('profileSidebar').classList.add('open');
            document.getElementById('profileSidebarStreak').innerText = globalDailyStreak;
            if (tg.initDataUnsafe?.user) {
                document.getElementById('profileSidebarName').innerText = `@${tg.initDataUnsafe.user.username || tg.initDataUnsafe.user.first_name}`;
                document.querySelector('[data-i18n="playerId"]').innerText = `${currentLang === 'en' ? 'Player' : 'Игрок'} #${tg.initDataUnsafe.user.id}`;
            }
        }
        function closeProfile() {
            document.getElementById('profileSidebar').classList.remove('open');
        }

        function toggleTheme(checkbox) {
            const theme = checkbox.checked ? 'platinum' : 'dark';
            if (theme === 'platinum') {
                document.documentElement.setAttribute('data-theme', 'platinum');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
            if (tg.CloudStorage) tg.CloudStorage.setItem('app_theme', theme);
            tg.HapticFeedback.selectionChanged();
        }

        const scoreElement = document.getElementById('score');
        const profileScoreElement = document.getElementById('profileScore');
        const tapBtn = document.getElementById('tapBtn');
        const energyText = document.getElementById('energyText');
        const energyBar = document.getElementById('energyBar');

        let serverTaps = 0; let serverBonus = 0; 
        let pendingStandardClicks = 0; let pendingRocketClicks = 0;
        let inFlightStandardClicks = 0; let inFlightRocketClicks = 0;
        
        let currentLbTab = 'players'; let currentMySquad = ''; 
        let globalDailyStreak = 0; let globalLastClaimDate = "";
        let globalClaimedSponsors = []; let globalDailyTaps = 0; let globalQuestClaimed = 0;
        let sponsorStates = { 1: "init", 2: "init", 3: "init", 4: "init" }; 

        const refsCount = parseInt(urlParams.get('refs')) || 0;
        let isRocketActive = false;
        
        let isPremium = tg.initDataUnsafe?.user?.is_premium || false;
        let maxTurbineCharges = isPremium ? 2 : 1;
        let maxRockets = isPremium ? 3 : 2;
        let currentTurbineCharges = maxTurbineCharges; 
        let rocketsLeft = maxRockets;

        let multitapLevel = 1; let maxEnergyLevel = 1; let autoBotLevel = 0; let energy = 1000; let maxEnergy = 1000; 
        let currentRoomLevel = 0; let ownedArtifactIds = ['default']; let currentArtifactId = 'default';
        let ownedArenaThemes = ['meme'];
        let currentArenaTheme = 'meme';

        const ARENA_THEMES = [
            { id: 'meme', name: '🐸 Мемная Драма', cost: 0, desc: 'Классика Telegram. Плачущий Пепе при поражении и дождь из денег при победе.', color: 'transparent', borderColor: '#fbbf24', textColor: '#fbbf24' },
            { id: 'crypto', name: '📈 Крипто-Биржа', cost: 1000000, desc: 'Строгий PnL интерфейс. Японские свечи, выбивающие противника, и биржевые статусы.', color: 'linear-gradient(90deg, #10b981, #059669)', borderColor: 'transparent', textColor: 'white' },
            { id: 'cyber', name: '💥 Кибер-Арена', cost: 5000000, desc: 'Эксклюзив для хайроллеров. Экран противника разлетается на пиксели, неоновое FATALITY.', color: 'linear-gradient(90deg, #ef4444, #dc2626)', borderColor: 'rgba(239, 68, 68, 0.4)', textColor: 'white', extraStyle: 'background: radial-gradient(circle at top right, rgba(239, 68, 68, 0.1), rgba(20,20,25,0.9));' }
        ];

        const BASE_ROOM_BG = 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/0lvl.png';
        const ROOM_LEVELS = [
            { level: 1, name: 'Стартовая студия', cost: 15000, income: 3, bgImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/1lvl.png', previewImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/1lvl.png' },
            { level: 2, name: 'Офис', cost: 500000, income: 6, bgImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/2lvl.png', previewImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/2lvl.png' },
            { level: 3, name: 'Кибер-люкс', cost: 1500000, income: 12, bgImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/3lvl.png', previewImg: 'https://raw.githubusercontent.com/07810868436g-rgb/grubot/main/3lvl.png' }
        ];

        const LEAGUES_CONFIG = [
            { minScore: 0, name: 'Wood (Noob)', color: '#a3a3a3' }, { minScore: 10000, name: 'Bronze (Guest)', color: '#cd7f32' },
            { minScore: 100000, name: 'Silver (Player)', color: '#e2e8f0' }, { minScore: 1000000, name: 'Gold (Pro)', color: '#fbbf24' },
            { minScore: 10000000, name: 'Diamond', color: '#38bdf8' }
        ];

        const ARTIFACTS = [
            { id: 'default', name: 'Без артефакта', cost: 0, img: '', effectText: '', bonus: 0 },
            { id: 'pepe', name: 'Жаба Pepe', cost: 50000, img: 'https://img.icons8.com/color/512/pepe-the-frog.png', effectText: '+3 к тапу', bonus: 3 },
            { id: 'spotty', name: 'Собака Spotty', cost: 250000, img: 'https://img.icons8.com/color/512/dog.png', effectText: '+5 к тапу', bonus: 5 },
            { id: 'durov_cap', name: 'Кепка Дурова', cost: 1000000, img: 'https://img.icons8.com/color/512/baseball-cap.png', effectText: '+15 к тапу', bonus: 15 }
        ];

        if (tg.initDataUnsafe?.user) { document.getElementById('userName').innerText = `@${tg.initDataUnsafe.user.username || tg.initDataUnsafe.user.first_name}`; }
        document.getElementById('taskFriendsCount').innerText = refsCount;
        document.getElementById('turbineChargesUI').innerText = `${currentTurbineCharges}/${maxTurbineCharges}`;
        document.getElementById('rocketCount').innerText = `${rocketsLeft}/${maxRockets}`;

        function showFloatingEffects(x, y, amount, isRocket) {
            let num = document.createElement('div');
            num.className = 'floating-text'; num.innerText = `+${amount}`;
            num.style.left = `${x - 20}px`; num.style.top = `${y - 40}px`;
            num.style.color = isRocket ? '#f59e0b' : '#ffffff';
            num.style.animation = 'none';
            document.body.appendChild(num);

            const curveDirection = Math.random() < 0.5 ? -1 : 1;
            const endX = curveDirection * (20 + Math.random() * 45);
            const controlX = curveDirection * (45 + Math.random() * 60);
            const endY = -(130 + Math.random() * 40);
            const controlY = -(55 + Math.random() * 35);
            const pointOnCurve = (t) => {
                const inverseT = 1 - t;
                return {
                    x: inverseT * inverseT * 0 + 2 * inverseT * t * controlX + t * t * endX,
                    y: inverseT * inverseT * 0 + 2 * inverseT * t * controlY + t * t * endY
                };
            };

            num.animate([0, 0.35, 0.7, 1].map((offset) => {
                const point = pointOnCurve(offset);
                return {
                    offset,
                    opacity: 1 - offset,
                    transform: `translate(${point.x}px, ${point.y}px) scale(${1 + offset * 0.2})`
                };
            }), { duration: 900, easing: 'ease-out', fill: 'forwards' });
            setTimeout(() => num.remove(), 900);

            for(let i = 0; i < 4; i++) {
                let spark = document.createElement('div');
                spark.className = 'spark';
                spark.style.left = x + 'px'; spark.style.top = y + 'px';
                spark.style.setProperty('--dx', (Math.random() * 80 - 40) + 'px');
                spark.style.setProperty('--dy', (Math.random() * 80 - 40) + 'px');
                document.body.appendChild(spark);
                setTimeout(() => spark.remove(), 600);
            }
        }

        function showToast(message, type = 'info') {
            let container = document.getElementById('toastContainer');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toastContainer';
                container.setAttribute('aria-live', 'polite');
                container.setAttribute('aria-atomic', 'true');
                document.body.appendChild(container);
            }

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
            toast.textContent = message;
            container.appendChild(toast);

            setTimeout(() => {
                toast.classList.add('toast-hiding');
                setTimeout(() => toast.remove(), 250);
            }, 3500);
        }

        function getCurrentUserLeague(score) { let current = LEAGUES_CONFIG[0]; for (let i = 0; i < LEAGUES_CONFIG.length; i++) { if (score >= LEAGUES_CONFIG[i].minScore) { current = LEAGUES_CONFIG[i]; } } return current; }
        function getUpgradeCost(baseCost, currentLevel) { return baseCost * Math.pow(2, currentLevel - (baseCost === 5000 && currentLevel === 0 ? 0 : 1)); }

        function openSheet(sheetId) {
            document.getElementById('globalOverlay').style.display = 'block';
            setTimeout(() => { 
                document.getElementById('globalOverlay').style.opacity = '1';
                document.getElementById(sheetId).classList.add('open'); 
            }, 10);
        }
        
        function closeAllSheets() {
            document.querySelectorAll('.sheet:not(#shopSheet)').forEach(sheet => sheet.classList.remove('open'));
            document.getElementById('globalOverlay').style.opacity = '0';
            setTimeout(() => { document.getElementById('globalOverlay').style.display = 'none'; }, 300);
        }

        function updateStudioVisuals() {
            let bgElement = document.getElementById('mainStudioBg');
            if (currentRoomLevel === 0) { bgElement.style.backgroundImage = `url('${BASE_ROOM_BG}')`; } 
            else { let room = ROOM_LEVELS.find(r => r.level === currentRoomLevel); if (room) bgElement.style.backgroundImage = `url('${room.bgImg}')`; }
            let income = ROOM_LEVELS.find(r => r.level === currentRoomLevel)?.income || 0;
            document.getElementById('studioIncomeTotal').innerText = income.toLocaleString('ru-RU');
        }

        function openStudioShop() { document.getElementById('shopSheetOverlay').style.display = 'block'; setTimeout(() => { document.getElementById('shopSheetOverlay').style.opacity = '1'; document.getElementById('shopSheet').classList.add('open'); }, 10); renderShopItems(); }
        function closeStudioShop() { document.getElementById('shopSheet').classList.remove('open'); document.getElementById('shopSheetOverlay').style.opacity = '0'; setTimeout(() => { document.getElementById('shopSheetOverlay').style.display = 'none'; }, 300); }

        function renderShopItems() {
            const container = document.getElementById('shopItemsContainer'); container.innerHTML = '<div class="showcase-grid"></div>';
            const grid = container.querySelector('.showcase-grid');
            ROOM_LEVELS.forEach(room => {
                let isBought = currentRoomLevel >= room.level; let isNext = currentRoomLevel + 1 === room.level; let isLocked = room.level > currentRoomLevel + 1;
                let btnHtml = ''; let cardClass = 'showcase-card';
                if (isBought) { cardClass += ' bought'; btnHtml = `<button class="showcase-btn btn-gray" disabled>${currentLang === 'en' ? 'Equipped ✅' : 'Установлено ✅'}</button>`; } 
                else if (isLocked) { cardClass += ' locked'; btnHtml = `<button class="showcase-btn btn-gray" disabled>🔒 ${currentLang === 'en' ? 'Requires Level' : 'Нужен уровень'} ${room.level - 1}</button>`; } 
                else if (isNext) { btnHtml = `<button id="btnBuyRoom${room.level}" class="showcase-btn btn-green" onclick="processPurchase(() => buyRoomLevel(${room.level}, this))">${currentLang === 'en' ? 'Buy for' : 'Купить за'} ${room.cost.toLocaleString('ru-RU')} $ROB</button>`; }
                grid.insertAdjacentHTML('beforeend', `<div class="${cardClass}"><div class="showcase-img-container"><img src="${room.previewImg}" class="showcase-img"></div><div class="showcase-info"><div class="showcase-title">${room.name} (${currentLang === 'en' ? 'Lvl' : 'Ур.'} ${room.level})</div><div class="showcase-effect">+${room.income} $ROB/sec</div>${btnHtml}</div></div>`);
            });
        }

        function processPurchase(buyFunction) {
            if (pendingStandardClicks > 0 || pendingRocketClicks > 0 || inFlightStandardClicks > 0 || inFlightRocketClicks > 0) {
                if (pendingStandardClicks > 0 || pendingRocketClicks > 0) syncWithServer(false);
                setTimeout(() => processPurchase(buyFunction), 500); 
            } else { buyFunction(); }
        }

        function buyRoomLevel(levelId, btnElement) {
            const originalText = btnElement.innerText; btnElement.innerText = "⏳..."; btnElement.disabled = true;
            fetch(`${BACKEND_URL}/buy`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, type: "room_upgrade", level: levelId }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") { serverTaps = data.new_taps_balance; serverBonus = data.new_bonus_balance; currentRoomLevel = levelId; updateVisualScore(); updateStudioVisuals(); renderShopItems(); if (tg.CloudStorage) tg.CloudStorage.setItem('current_room_level', currentRoomLevel.toString()); tg.HapticFeedback.notificationOccurred('success'); } 
                else { showToast(`❌ ${data.error}`, 'error'); btnElement.innerText = originalText; btnElement.disabled = false; }
            }).catch(() => { showToast("❌ Error.", 'error'); btnElement.innerText = originalText; btnElement.disabled = false; });
        }

        function updateTechGridVisuals() { document.getElementById('gridMultitapLvl').innerText = `${currentLang === 'en' ? 'Lvl' : 'Ур.'} ${multitapLevel}`; document.getElementById('gridEnergyLvl').innerText = `${currentLang === 'en' ? 'Lvl' : 'Ур.'} ${maxEnergyLevel}`; document.getElementById('gridBotLvl').innerText = `${currentLang === 'en' ? 'Lvl' : 'Ур.'} ${autoBotLevel}`; }

        function openTechModal(type) {
            const title = document.getElementById('techModalTitle'); const desc = document.getElementById('techModalDesc'); const icon = document.getElementById('techModalIcon'); const current = document.getElementById('techModalCurrent'); const next = document.getElementById('techModalNext'); const btn = document.getElementById('techModalBuyBtn');
            if (type === 'multitap') { icon.innerText = "👆"; title.innerText = currentLang === 'en' ? 'Multitap' : "Мультитап"; desc.innerText = currentLang === 'en' ? 'Increases earn per tap.' : "Увеличивает добычу за 1 тап."; current.innerText = `+${multitapLevel}`; next.innerText = `+${multitapLevel + 1}`; btn.innerText = `${currentLang === 'en' ? 'Upgrade' : 'Прокачать'} • ${getUpgradeCost(2000, multitapLevel).toLocaleString('ru-RU')} $ROB`; } 
            else if (type === 'energy') { icon.innerText = "🔋"; title.innerText = currentLang === 'en' ? 'Energy Capacity' : "Энергоемкость"; desc.innerText = currentLang === 'en' ? 'Increases max energy limit.' : "Увеличивает запас энергии."; current.innerText = `${maxEnergy}`; next.innerText = `${1000 + (maxEnergyLevel * 500)}`; btn.innerText = `${currentLang === 'en' ? 'Upgrade' : 'Прокачать'} • ${getUpgradeCost(2000, maxEnergyLevel).toLocaleString('ru-RU')} $ROB`; } 
            else if (type === 'bot') { icon.innerText = "🤖"; title.innerText = currentLang === 'en' ? 'Auto-Bot' : "Авто-Бот"; desc.innerText = currentLang === 'en' ? 'Gathers passive income while offline (max 3h).' : "Студия приносит доход пока вы офлайн (макс 3 часа)."; current.innerText = `+${autoBotLevel}/sec`; next.innerText = `+${autoBotLevel + 1}/sec`; let cost = autoBotLevel === 0 ? 5000 : getUpgradeCost(5000, autoBotLevel + 1); btn.innerText = `${autoBotLevel === 0 ? (currentLang === 'en' ? 'Buy Bot' : 'Купить бота') : (currentLang === 'en' ? 'Upgrade' : 'Прокачать')} • ${cost.toLocaleString('ru-RU')} $ROB`; }
            btn.onclick = () => { processPurchase(() => buyTechBoost(type, btn)); }; document.getElementById('techModal').style.display = 'flex';
        }
        function closeTechModal() { document.getElementById('techModal').style.display = 'none'; }

        function buyTechBoost(type, btnElement) {
            const originalText = btnElement.innerText; btnElement.innerText = "⏳..."; btnElement.disabled = true;
            fetch(`${BACKEND_URL}/buy`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, type: "tech", item_id: type }) })
            .then(res => res.json()).then(data => {
                btnElement.innerText = originalText; btnElement.disabled = false;
                if (data.status === "success") {
                    serverTaps = data.new_taps_balance; serverBonus = data.new_bonus_balance;
                    if (type === 'multitap') { multitapLevel++; if (tg.CloudStorage) tg.CloudStorage.setItem('multitap_level', multitapLevel.toString()); }
                    else if (type === 'energy') { maxEnergyLevel++; maxEnergy = 1000 + ((maxEnergyLevel - 1) * 500); document.getElementById('maxEnergyUI').innerText = maxEnergy; updateEnergyVisual(); if (tg.CloudStorage) tg.CloudStorage.setItem('max_energy_level', maxEnergyLevel.toString()); }
                    else if (type === 'bot') { autoBotLevel++; updateStudioVisuals(); if (tg.CloudStorage) tg.CloudStorage.setItem('bot_level', autoBotLevel.toString()); }
                    updateTechGridVisuals(); updateVisualScore(); tg.HapticFeedback.notificationOccurred('success'); closeTechModal();
                } else { showToast(`❌ ${data.error}`, 'error'); }
            }).catch(() => { btnElement.innerText = originalText; btnElement.disabled = false; showToast("❌ Error.", 'error'); });
        }

        function renderArtifacts() {
            const container = document.getElementById('artifactsContainer'); container.innerHTML = '';
            ARTIFACTS.forEach(art => {
                if (art.id === 'default') return; 
                const isOwned = ownedArtifactIds.includes(art.id); const isEquipped = currentArtifactId === art.id; let btnHTML = ''; let cardClass = 'artifact-card';
                if (isEquipped) { cardClass += ' equipped'; btnHTML = `<button class="artifact-btn btn-equipped">${currentLang === 'en' ? 'Equipped' : 'Надето'}</button>`; } 
                else if (isOwned) { btnHTML = `<button class="artifact-btn btn-select" onclick="selectArtifact('${art.id}')">${currentLang === 'en' ? 'Equip' : 'Надеть'}</button>`; } 
                else { btnHTML = `<button class="artifact-btn btn-buy" onclick="processPurchase(() => buyArtifact('${art.id}', this))">${currentLang === 'en' ? 'Buy' : 'Купить'}<br>${art.cost.toLocaleString('ru-RU')} $ROB</button>`; }
                container.insertAdjacentHTML('beforeend', `<div class="${cardClass}"><img src="${art.img}" class="artifact-img"><div class="artifact-name">${art.name}</div><div class="artifact-effect">${art.effectText}</div>${btnHTML}</div>`);
            });
            const activeArt = ARTIFACTS.find(a => a.id === currentArtifactId) || ARTIFACTS[0];
            const overlay = document.getElementById('activeArtifactOverlay');
            if (activeArt.img) { overlay.src = activeArt.img; overlay.style.display = 'block'; } else { overlay.style.display = 'none'; }
        }

        function selectArtifact(artId) { if (ownedArtifactIds.includes(artId)) { currentArtifactId = artId; renderArtifacts(); if (tg.CloudStorage) tg.CloudStorage.setItem('current_artifact', currentArtifactId); tg.HapticFeedback.selectionChanged(); } }
        
        function buyArtifact(artId, btnElement) { 
            const originalText = btnElement.innerHTML; btnElement.innerHTML = "⏳..."; btnElement.disabled = true;
            fetch(`${BACKEND_URL}/buy`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, type: "skin", item_id: artId }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") { serverTaps = data.new_taps_balance; serverBonus = data.new_bonus_balance; ownedArtifactIds.push(artId); currentArtifactId = artId; updateVisualScore(); renderArtifacts(); if (tg.CloudStorage) { tg.CloudStorage.setItem('owned_skins', JSON.stringify(ownedArtifactIds)); tg.CloudStorage.setItem('current_artifact', currentArtifactId); } tg.HapticFeedback.notificationOccurred('success'); } 
                else { showToast(`❌ ${data.error}`, 'error'); btnElement.innerHTML = originalText; btnElement.disabled = false; }
            }).catch(() => { showToast("❌ Error.", 'error'); btnElement.innerHTML = originalText; btnElement.disabled = false; });
        }

        function renderArenaStyles() {
            const container = document.getElementById('arenaStylesContainer');
            if(!container) return;
            container.innerHTML = '';
            
            ARENA_THEMES.forEach(theme => {
                const isOwned = ownedArenaThemes.includes(theme.id); 
                const isEquipped = currentArenaTheme === theme.id; 
                
                let btnHTML = '';
                let cardClass = isEquipped ? 'arena-style-card equipped' : 'arena-style-card';
                let extraCSS = theme.extraStyle ? theme.extraStyle : '';
                
                if (isEquipped) { 
                    btnHTML = `<button class="support-btn" style="padding: 10px; background: transparent; border: 1px solid var(--gold); color: var(--gold); box-shadow: none;">${currentLang === 'en' ? 'Equipped ✅' : 'Выбрано ✅'}</button>`; 
                } 
                else if (isOwned) { 
                    btnHTML = `<button class="support-btn" style="padding: 10px; background: var(--panel-border); color: var(--text-main); box-shadow: none;" onclick="selectArenaTheme('${theme.id}')">${currentLang === 'en' ? 'Equip' : 'Применить'}</button>`; 
                } 
                else { 
                    btnHTML = `<button class="support-btn" style="padding: 10px; background: ${theme.color}; color: ${theme.textColor}; border: ${theme.borderColor === 'transparent' ? 'none' : '1px solid ' + theme.borderColor};" onclick="processPurchase(() => buyArenaTheme('${theme.id}', this))">${currentLang === 'en' ? 'Buy' : 'Купить'} ${theme.cost === 0 ? '' : theme.cost.toLocaleString('ru-RU')}</button>`; 
                }
                
                let priceText = theme.cost === 0 ? (currentLang === 'en' ? 'Free' : 'Бесплатно') : theme.cost.toLocaleString('ru-RU') + ' $ROB';
                let priceColor = theme.id === 'cyber' ? '#ef4444' : (theme.id === 'meme' ? 'var(--text-muted)' : '#10b981');
                
                container.insertAdjacentHTML('beforeend', `
                    <div class="${cardClass}" style="${extraCSS}">
                        <div class="style-header">
                            <div class="style-name">${theme.name}</div>
                            <div class="style-price" style="color: ${priceColor};">${priceText}</div>
                        </div>
                        <div class="style-desc">${theme.desc}</div>
                        ${btnHTML}
                    </div>
                `);
            });
        }

        function selectArenaTheme(themeId) { 
            if (ownedArenaThemes.includes(themeId)) { 
                currentArenaTheme = themeId; 
                renderArenaStyles(); 
                if (tg.CloudStorage) tg.CloudStorage.setItem('current_arena_theme', currentArenaTheme); 
                tg.HapticFeedback.selectionChanged(); 
            } 
        }

        function buyArenaTheme(themeId, btnElement) { 
            const originalText = btnElement.innerHTML; btnElement.innerHTML = "⏳..."; btnElement.disabled = true;
            fetch(`${BACKEND_URL}/buy`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, type: "arena_theme", item_id: themeId }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") { 
                    serverTaps = data.new_taps_balance; serverBonus = data.new_bonus_balance; 
                    ownedArenaThemes.push(themeId); 
                    currentArenaTheme = themeId; 
                    updateVisualScore(); 
                    renderArenaStyles(); 
                    if (tg.CloudStorage) { tg.CloudStorage.setItem('current_arena_theme', currentArenaTheme); } 
                    tg.HapticFeedback.notificationOccurred('success'); 
                } 
                else { showToast(`❌ ${data.error}`, 'error'); btnElement.innerHTML = originalText; btnElement.disabled = false; }
            }).catch(() => { showToast("❌ Error.", 'error'); btnElement.innerHTML = originalText; btnElement.disabled = false; });
        }

        function updateLevelVisuals(totalScore) {
            let league = getCurrentUserLeague(totalScore); 
            const leagueUi = document.getElementById('userLeagueName'); leagueUi.innerText = league.name; leagueUi.style.color = league.color;
            document.getElementById('profileSidebarLeague').innerText = league.name;
            document.getElementById('profileSidebarLeague').style.color = league.color;
            
            if (currentMySquad !== '') { document.getElementById('mySquadInfo').style.display = 'block'; document.getElementById('mySquadNameText').innerText = currentMySquad; } else { document.getElementById('mySquadInfo').style.display = 'none'; }
        }

        function closeOfflineModal() { document.getElementById('offlineModal').style.display = 'none'; tg.HapticFeedback.notificationOccurred('success'); }
        
        function switchLeaderboardTab(tab) {
            currentLbTab = tab; 
            document.getElementById('tabPlayers').classList.toggle('active', tab === 'players'); 
            document.getElementById('tabSquads').classList.toggle('active', tab === 'squads'); 
            document.getElementById('createSquadContainer').style.display = tab === 'squads' ? 'block' : 'none'; 
            loadLeaderboard();
        }

        function activateRocket() {
            if (rocketsLeft <= 0) { showToast(currentLang === 'en' ? "❌ Out of rockets!" : "❌ Ракеты закончились!"); return; }
            if (isRocketActive) { return; }
            let btn = document.getElementById('btnActivateRocket'); const origText = btn.innerText; btn.innerText = "⏳..."; btn.disabled = true;
            fetch(`${BACKEND_URL}/activate-rocket`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") {
                    rocketsLeft = data.rockets_left; document.getElementById('rocketCount').innerText = `${rocketsLeft}/${maxRockets}`;
                    if (rocketsLeft <= 0) { btn.innerText = currentLang === 'en' ? "Finished ❌" : "Закончились ❌"; btn.style.background = "var(--panel-border)"; btn.disabled = true; }
                    else { btn.innerText = origText; btn.disabled = false; }
                    isRocketActive = true; document.getElementById('rocketBadge').style.display = 'block'; showScreen('main', document.querySelector('.menu-btn'));
                    let timeLeft = 15; document.getElementById('rocketTimer').innerText = timeLeft;
                    let countdown = setInterval(() => { timeLeft--; document.getElementById('rocketTimer').innerText = timeLeft; if (timeLeft <= 0) { clearInterval(countdown); isRocketActive = false; document.getElementById('rocketBadge').style.display = 'none'; } }, 1000);
                    tg.HapticFeedback.notificationOccurred('success');
                } else { showToast(`❌ ${data.error}`, 'error'); btn.innerText = origText; btn.disabled = false; }
            }).catch(() => { btn.innerText = origText; btn.disabled = false; showToast("❌ Error.", 'error'); });
        }

        function generateSquadLink() { 
            let val = document.getElementById('squadInput').value.trim(); if(!val) return; 
            let btn = document.getElementById('btnCreateSquad'); const originalText = btn.innerText; btn.innerText = "⏳..."; btn.disabled = true;
            fetch(`${BACKEND_URL}/create-squad`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, channel: val }) })
            .then(res => res.json()).then(data => {
                btn.innerText = originalText; btn.disabled = false;
                if(data.status === "success") { document.getElementById('squadLinkResult').style.display = 'block'; document.getElementById('generatedSquadLink').innerText = data.link; tg.HapticFeedback.notificationOccurred('success'); } else { showToast(`❌ ${data.error}`, 'error'); }
            }).catch(() => { btn.innerText = originalText; btn.disabled = false; showToast("❌ Error.", 'error'); });
        }

        function showScreen(screenId, btnElement) { document.querySelectorAll('.screen').forEach(s => s.classList.remove('active')); document.querySelectorAll('.menu-btn').forEach(b => b.classList.remove('active')); document.getElementById(screenId).classList.add('active'); btnElement.classList.add('active'); if (screenId === 'top') loadLeaderboard(); }
        function showCreateSquadModal() { document.getElementById('squadModal').style.display = 'flex'; document.getElementById('squadLinkResult').style.display = 'none'; document.getElementById('squadInput').value = ''; }
        function closeSquadModal() { document.getElementById('squadModal').style.display = 'none'; }
        function copySquadLink() { let link = document.getElementById('generatedSquadLink').innerText; if (navigator.clipboard) { navigator.clipboard.writeText(link).then(() => { showToast("✅ Copied!"); closeSquadModal(); }).catch(() => { showToast("🔗 Link: " + link); }); } else { showToast("🔗 Link: " + link); } }

        function loadLeaderboard() {
            const listContainer = document.getElementById('leaderboardList'); listContainer.innerHTML = `<div style="color: var(--text-muted); padding: 20px;">${currentLang === 'en' ? 'Loading leaders...' : 'Загрузка списка лидеров...'}</div>`;
            fetch(`${BACKEND_URL}/leaderboard`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, tab: currentLbTab }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") {
                    listContainer.innerHTML = ''; 
                    if (data.tab === "players") {
                        data.list.forEach((player, index) => {
                            const rank = index + 1; let rankDisplay = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`; 
                            let bgStyle = player.isMe ? 'background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.4);' : 'background: var(--panel-bg); border: 1px solid var(--panel-border);'; 
                            listContainer.insertAdjacentHTML('beforeend', `<div style="display: flex; justify-content: space-between; align-items: center; padding: 14px; border-radius: 14px; margin-bottom: 8px; ${bgStyle}"><div style="font-size: 18px; font-weight: 900; color: var(--text-muted); width: 35px; text-align: center;">${rankDisplay}</div><div style="flex-grow: 1; text-align: left; font-weight: bold; font-size: 15px; margin-left: 10px; color: var(--text-main);">${player.name}</div><div style="font-weight: bold; color: var(--gold); font-size: 15px;">${player.score.toLocaleString('ru-RU')}</div></div>`);
                            if(player.isMe) document.getElementById('rankPlaceholder').innerText = rank;
                        });
                    } else if (data.tab === "squads") {
                        data.list.forEach((squad, index) => {
                            const rank = index + 1; let rankDisplay = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`; 
                            let isClickable = rank <= 5; let opacity = isClickable ? '1' : '0.6'; let borderStyle = squad.isMySquad ? '1px solid var(--gold)' : '1px solid var(--panel-border)'; let bgStyle = squad.isMySquad ? 'background: rgba(251, 191, 36, 0.08);' : 'background: var(--panel-bg);'; 
                            let actionHtml = isClickable ? `<button class="support-btn" style="margin: 0; padding: 6px 12px; font-size: 12px; background: linear-gradient(90deg, #10b981, #059669);" onclick="tg.openTelegramLink('https://t.me/${squad.id.replace('@', '')}')">${currentLang === 'en' ? 'Join' : 'Вступить'}</button>` : ''; 
                            listContainer.insertAdjacentHTML('beforeend', `<div style="display: flex; justify-content: space-between; align-items: center; padding: 14px; border-radius: 14px; margin-bottom: 8px; ${bgStyle} opacity: ${opacity}; border: ${borderStyle};"><div style="font-size: 18px; font-weight: 900; color: var(--text-muted); width: 35px; text-align: center;">${rankDisplay}</div><div style="flex-grow: 1; text-align: left; font-weight: bold; font-size: 14px; margin-left: 10px; color: var(--text-main);">${squad.id} ${squad.isMySquad ? '(You)' : ''}<br><span style="font-size: 11px; color: var(--text-muted);">👥 ${squad.members} ${currentLang === 'en' ? 'players' : 'игроков'}</span><br><span style="font-size: 12px; color: var(--gold); font-weight: bold;">${squad.score.toLocaleString('ru-RU')} $ROB</span></div><div>${actionHtml}</div></div>`);
                        });
                    }
                    if (data.list.length === 0) listContainer.innerHTML = `<div style="color: var(--text-muted); padding: 20px;">${currentLang === 'en' ? 'List is empty...' : 'Список пока пуст...'}</div>`;
                } else { listContainer.innerHTML = '<div style="color: #ef4444; padding: 20px;">Error loading leaderboard</div>'; }
            });
        }

        function getUnsyncedEarn() {
            let activeArt = ARTIFACTS.find(a => a.id === currentArtifactId) || ARTIFACTS[0];
            let baseEarn = multitapLevel + activeArt.bonus;
            let rocketEarn = baseEarn * 5;
            return (pendingStandardClicks + inFlightStandardClicks) * baseEarn + 
                   (pendingRocketClicks + inFlightRocketClicks) * rocketEarn;
        }

        function updateVisualScore() {
            let currentTotal = serverTaps + serverBonus + getUnsyncedEarn();
            scoreElement.innerText = currentTotal.toLocaleString('ru-RU'); 
            profileScoreElement.innerText = currentTotal.toLocaleString('ru-RU'); 
            updateLevelVisuals(currentTotal); 
        }

        function updateEnergyVisual() { energyText.innerText = Math.max(0, Math.floor(energy)); let percent = (Math.max(0, energy) / maxEnergy) * 100; energyBar.style.width = `${percent}%`; }
        function inviteFriend() { const userId = tg.initDataUnsafe?.user?.id; if (!userId) return; tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(`https://t.me/grutap_robot?start=ref_${userId}`)}&text=${encodeURIComponent("GruTap! 🚀")}`); }
        
        function renderDailyRewardUI() {
            document.getElementById('dailyStreakText').innerText = globalDailyStreak;
            let btn = document.getElementById('btnDailyReward');
            const todayStr = new Date().toISOString().slice(0, 10);
            
            if (globalLastClaimDate === todayStr) {
                btn.innerText = currentLang === 'en' ? "Claimed ✅" : "Забрано ✅"; btn.style.background = "var(--panel-border)"; btn.style.color = "var(--text-muted)"; btn.disabled = true;
            } else {
                let nextDay = (globalDailyStreak % 7) + 1;
                btn.innerText = `${currentLang === 'en' ? 'Claim' : 'Забрать'} +${nextDay * 100} $ROB`;
                btn.style.background = "var(--gold-grad)"; btn.style.color = "#000"; btn.disabled = false;
            }
        }

        function renderDailyQuestUI() {
            let visualDailyTaps = globalDailyTaps + getUnsyncedEarn();
            if (visualDailyTaps > 5000) visualDailyTaps = 5000;
            
            document.getElementById('dailyTapsText').innerText = visualDailyTaps;
            document.getElementById('dailyTapsBar').style.width = `${Math.min(100, (visualDailyTaps / 5000) * 100)}%`;
            
            let btn = document.getElementById('btnDailyQuest');
            if (globalQuestClaimed === 1 || globalQuestClaimed === true) {
                btn.innerText = currentLang === 'en' ? "Claimed ✅" : "Получено ✅"; btn.style.background = "var(--panel-border)"; btn.disabled = true; btn.style.color = "var(--text-muted)";
            } else if (visualDailyTaps >= 5000) {
                btn.innerText = `${currentLang === 'en' ? 'Claim' : 'Забрать'} 10 000 $ROB 🎁`; btn.style.background = "linear-gradient(90deg, #10b981, #059669)"; btn.disabled = false; btn.style.color = "white";
            } else {
                btn.innerText = currentLang === 'en' ? "Complete Goal 🎯" : "Выполни цель 🎯"; btn.style.background = "var(--panel-border)"; btn.disabled = true;
            }
        }

        function claimDailyServer() {
            let btn = document.getElementById('btnDailyReward');
            btn.innerText = "⏳..."; btn.disabled = true;
            fetch(`${BACKEND_URL}/daily-claim`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") {
                    globalDailyStreak = data.daily_streak; globalLastClaimDate = data.last_claim_date; serverBonus = data.new_bonus_balance;
                    updateVisualScore(); renderDailyRewardUI(); tg.HapticFeedback.notificationOccurred('success'); showToast(`🎉 Day ${data.daily_streak}! +${data.reward_received} $ROB!`);
                } else { showToast(`❌ ${data.error}`, 'error'); renderDailyRewardUI(); }
            }).catch(() => { showToast("❌ Error.", 'error'); renderDailyRewardUI(); });
        }

        function claimDailyQuestServer() {
            let btn = document.getElementById('btnDailyQuest');
            btn.innerText = "⏳..."; btn.disabled = true;
            fetch(`${BACKEND_URL}/claim-daily-quest`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") {
                    globalQuestClaimed = 1; serverBonus = data.new_bonus_balance;
                    updateVisualScore(); renderDailyQuestUI(); tg.HapticFeedback.notificationOccurred('success'); showToast("🎯 +10 000 $ROB!");
                } else { showToast(`❌ ${data.error}`, 'error'); renderDailyQuestUI(); }
            }).catch(() => { showToast("❌ Error.", 'error'); renderDailyQuestUI(); });
        }

        function renderSponsorsUI() {
            for(let id = 1; id <= 4; id++) {
                let btn = document.getElementById('btnSponsor' + id);
                if (!btn) continue;
                if (globalClaimedSponsors.includes(id)) {
                    btn.innerText = currentLang === 'en' ? "Completed ✅" : "Выполнено ✅"; btn.style.background = "var(--panel-border)"; btn.style.color = "var(--text-muted)"; btn.disabled = true;
                } else if (sponsorStates[id] === "clicked") {
                    btn.innerText = currentLang === 'en' ? "Verify 🔄" : "Проверить 🔄"; btn.style.background = "var(--gold-grad)"; btn.style.color = "#000";
                } else {
                    btn.innerText = currentLang === 'en' ? "Subscribe" : "Подписаться"; btn.style.background = "var(--gold-grad)"; btn.style.color = "#000"; btn.disabled = false;
                }
            }
        }

        function clickSponsor(id, url) {
            let btn = document.getElementById('btnSponsor' + id);
            if (sponsorStates[id] === "init") {
                tg.openTelegramLink(url); sponsorStates[id] = "clicked"; renderSponsorsUI();
            } else if (sponsorStates[id] === "clicked") {
                btn.innerText = "⏳..."; btn.disabled = true;
                fetch(`${BACKEND_URL}/claim-sponsor`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, sponsor_id: id }) })
                .then(res => res.json()).then(data => {
                    if (data.status === "success") {
                        globalClaimedSponsors.push(id); serverBonus = data.new_bonus_balance;
                        updateVisualScore(); renderSponsorsUI(); tg.HapticFeedback.notificationOccurred('success'); showToast("🎉 +450 $ROB!");
                    } else { showToast(`❌ ${data.error}`, 'error'); sponsorStates[id] = "init"; renderSponsorsUI(); }
                }).catch(() => { showToast("❌ Error.", 'error'); sponsorStates[id] = "init"; renderSponsorsUI(); });
            }
        }

        function finishLoading() { setLanguage(currentLang); updateTechGridVisuals(); updateStudioVisuals(); updateEnergyVisual(); renderArtifacts(); renderArenaStyles(); updateVisualScore(); syncWithServer(true); }

        if (tg.CloudStorage) {
            tg.CloudStorage.getItems(['multitap_level', 'max_energy_level', 'bot_level', 'owned_skins', 'current_artifact', 'current_room_level', 'current_arena_theme', 'app_theme'], (err, values) => {
                if (!err && values) {
                    if (values.multitap_level) multitapLevel = parseInt(values.multitap_level, 10) || 1;
                    if (values.max_energy_level) maxEnergyLevel = parseInt(values.max_energy_level, 10) || 1;
                    if (values.bot_level) autoBotLevel = parseInt(values.bot_level, 10) || 0;
                    if (values.current_room_level) currentRoomLevel = parseInt(values.current_room_level, 10) || 0;
                    if (values.owned_skins) { try { ownedArtifactIds = JSON.parse(values.owned_skins); } catch(e){} }
                    if (values.current_artifact) currentArtifactId = values.current_artifact;
                    if (values.current_arena_theme) currentArenaTheme = values.current_arena_theme;
                    
                    if (values.app_theme === 'platinum') {
                        document.documentElement.setAttribute('data-theme', 'platinum');
                        document.getElementById('themeSwitch').checked = true;
                    }

                    maxEnergy = 1000 + ((maxEnergyLevel - 1) * 500);
                }
                finishLoading();
            });
        } else { finishLoading(); }

        function shareResult(text) {
            if (tg.shareToStory) { 
                tg.shareToStory('https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000', { text: text }); 
            } else { 
                showToast("Скопируй для TikTok / Reels:\n\n" + text); 
            }
        }

        let audioContext, analyser, microphone, javascriptNode;
        let turbineActive = false; let turbineScore = 0; let turbineTimer = 10; let turbineInterval;

        async function startAudioTurbine() {
            if (currentTurbineCharges <= 0) {
                showToast(`❌ Заряды исчерпаны!\n\nОбычные: 1 в день\nPremium: 2 в день.\n\nВозвращайтесь завтра!`);
                return;
            }
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                document.getElementById('turbineArena').style.display = 'flex';
                document.getElementById('turbineActiveState').style.display = 'block';
                document.getElementById('turbineResultState').style.display = 'none';
                
                turbineScore = 0; turbineTimer = 10; document.getElementById('turbineScore').innerText = '0';
                turbineActive = true;
                
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                microphone = audioContext.createMediaStreamSource(stream);
                javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);
                
                analyser.smoothingTimeConstant = 0.8; analyser.fftSize = 1024;
                microphone.connect(analyser); analyser.connect(javascriptNode); javascriptNode.connect(audioContext.destination);
                
                javascriptNode.onaudioprocess = function() {
                    if(!turbineActive) return;
                    let array = new Uint8Array(analyser.frequencyBinCount); analyser.getByteFrequencyData(array);
                    let values = 0, length = array.length;
                    for (let i = 0; i < length; i++) values += (array[i]);
                    let average = values / length; 
                    
                    let percent = Math.min(100, average * 1.5);
                    document.getElementById('turbineFill').style.background = `conic-gradient(#ef4444 ${percent}%, transparent ${percent}%)`;
                    
                    if (average > 20) { 
                        let earned = Math.floor(average);
                        turbineScore += earned; 
                        document.getElementById('turbineScore').innerText = turbineScore.toLocaleString('ru-RU'); 
                    }
                }
                turbineInterval = setInterval(() => {
                    turbineTimer--; document.getElementById('turbineTimer').innerText = turbineTimer;
                    if(turbineTimer <= 0) endAudioTurbine(stream);
                }, 1000);
            } catch (err) { showToast("Нужен доступ к микрофону!"); }
        }

        function endAudioTurbine(stream) {
            clearInterval(turbineInterval); turbineActive = false;
            stream.getTracks().forEach(track => track.stop());
            if(audioContext) audioContext.close(); 
            document.getElementById('turbineActiveState').style.display = 'none';
            document.getElementById('turbineResultState').style.display = 'block';
            document.getElementById('turbineFinalScore').innerText = turbineScore.toLocaleString('ru-RU');
        }

        function claimAndExitTurbine(share = false) {
            let btn1 = document.getElementById('btnTurbineExit');
            let btn2 = document.getElementById('btnTurbineShare');
            if(btn1) btn1.disabled = true; if(btn2) btn2.disabled = true;

            fetch(`${BACKEND_URL}/turbine-claim`, { 
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, amount: turbineScore }) 
            }).then(res => res.json()).then(data => {
                if(btn1) btn1.disabled = false; if(btn2) btn2.disabled = false;
                if (data.status === "success") {
                    serverBonus = data.new_bonus_balance;
                    currentTurbineCharges = data.turbine_charges;
                    maxTurbineCharges = data.max_charges;
                    document.getElementById('turbineChargesUI').innerText = `${currentTurbineCharges}/${maxTurbineCharges}`;
                    updateVisualScore();
                    document.getElementById('turbineArena').style.display = 'none';
                    tg.HapticFeedback.notificationOccurred('success');
                    if(share) { shareResult(`🚀 Я надул ${turbineScore.toLocaleString('ru-RU')} $ROB в турбине! Попробуй обогнать меня! Ссылка в профиле.`); }
                } else { showToast(`❌ ${data.error}`, 'error'); document.getElementById('turbineArena').style.display = 'none'; }
            }).catch(() => { 
                if(btn1) btn1.disabled = false; if(btn2) btn2.disabled = false;
                showToast("❌ Ошибка сервера."); document.getElementById('turbineArena').style.display = 'none'; 
            });
        }

        function claimAndShareTurbine() { claimAndExitTurbine(true); }

        function openPvPModal() { document.getElementById('pvpSetupModal').style.display = 'flex'; }
        function closePvPModal() { document.getElementById('pvpSetupModal').style.display = 'none'; }
        function setPvPBet(amount) { document.getElementById('pvpBetInput').value = amount; }
        function setPvPBetPercent(pct) {
            let currentTotal = serverTaps + serverBonus + getUnsyncedEarn();
            let calcAmount = Math.floor(currentTotal * pct);
            document.getElementById('pvpBetInput').value = calcAmount > 0 ? calcAmount : 0;
        }

        function selectPvPMode(mode, btn) { pvpMode = mode; document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); }

        function startPvPSearch() {
            pvpBet = parseInt(document.getElementById('pvpBetInput').value) || 0;
            if (pvpBet < 100) { showToast("Минимальная ставка 100 $ROB!"); return; }
            let currentTotal = serverTaps + serverBonus + getUnsyncedEarn();
            if (currentTotal < pvpBet) { showToast("Мало денег на балансе!"); return; }
            closePvPModal();
            showToast("Ищем противника...");
            setTimeout(() => initBattle(), 2000);
        }

        async function initBattle() {
            myPos = 50; pvpTimer = 15;
            document.getElementById('pvpArena').style.display = 'flex';
            document.getElementById('pvpDivider').style.top = '50%';
            document.getElementById('pvpTimer').innerText = '15';
            document.getElementById('pvpMicHint').style.display = pvpMode === 'voice' ? 'block' : 'none';

            if(pvpMode === 'voice') {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser(); microphone = audioContext.createMediaStreamSource(stream); javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);
                    microphone.connect(analyser); analyser.connect(javascriptNode); javascriptNode.connect(audioContext.destination);
                    javascriptNode.onaudioprocess = function() {
                        let array = new Uint8Array(analyser.frequencyBinCount); analyser.getByteFrequencyData(array);
                        let avg = array.reduce((a,b) => a+b, 0) / array.length;
                        if(avg > 30) moveRope(avg * 0.05); 
                    }
                } catch(e) {
                    showToast("Нет доступа к микрофону!"); endBattle(true);
                }
            }

            pvpInterval = setInterval(() => {
                pvpTimer--; document.getElementById('pvpTimer').innerText = pvpTimer;
                moveRope(-1); 
                if(pvpTimer <= 0) endBattle();
            }, 1000);
        }

        function pvpPlayerTap() { if(pvpMode === 'touch') { moveRope(2); tg.HapticFeedback.impactOccurred('light'); } }

        function moveRope(amount) {
            myPos = Math.max(0, Math.min(100, myPos + amount));
            document.getElementById('pvpDivider').style.top = `${100 - myPos}%`;
            document.getElementById('pvpBottom').style.flexBasis = `${myPos}%`;
            document.getElementById('pvpTop').style.flexBasis = `${100 - myPos}%`;
        }

        let lastPvPWinAmount = 0;
        function endBattle(forceLose = false) {
            clearInterval(pvpInterval);
            if(pvpMode === 'voice' && audioContext) { audioContext.close(); }
            document.getElementById('pvpArena').style.display = 'none';
            
            let isWin = !forceLose && myPos > 50;
            
            fetch(`${BACKEND_URL}/pvp-result`, { 
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, bet: pvpBet, is_win: isWin }) 
            }).then(res => res.json()).then(data => {
                if (data.status === "success") {
                    serverTaps = data.new_taps_balance;
                    serverBonus = data.new_bonus_balance;
                    updateVisualScore();
                    showCustomPvPResult(isWin); 
                } else { showToast(`❌ ${data.error}`, 'error'); }
            }).catch(() => { showToast("❌ Ошибка соединения с сервером."); });
        }

        function showCustomPvPResult(isWin) {
            const resScreen = document.getElementById('pvpResultScreen');
            const icon = document.getElementById('pvpResultIcon');
            const title = document.getElementById('pvpResultTitle');
            const desc = document.getElementById('pvpResultDesc');
            const amount = document.getElementById('pvpResultAmount');
            const btnShare = document.getElementById('btnPvPShare');
            const btnExit = document.getElementById('btnPvPExit');
            
            resScreen.style.display = 'flex';
            lastPvPWinAmount = isWin ? Math.floor(pvpBet * 1.95) : pvpBet;
            
            if (currentArenaTheme === 'meme') {
                resScreen.style.background = isWin ? 'rgba(20, 40, 20, 0.95)' : 'rgba(20, 20, 20, 0.95) grayscale(100%)';
                icon.innerText = isWin ? '🐸👑' : '🐸💧';
                title.innerText = isWin ? 'ГГ, ИЗИ! (GG WP)' : 'Реквием по балансу...';
                title.style.color = isWin ? '#fbbf24' : '#a1a1aa';
                title.style.textShadow = 'none';
                desc.innerText = isWin ? 'Дождь из денег!' : 'Ты слил ставку.';
                amount.innerText = isWin ? `+ ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB` : `- ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB`;
                amount.style.color = isWin ? '#10b981' : '#ef4444';
                btnShare.style.display = isWin ? 'block' : 'none';
                btnExit.innerText = isWin ? 'Забрать банк' : 'Уйти в слезах';
            } 
            else if (currentArenaTheme === 'crypto') {
                resScreen.style.background = isWin ? 'radial-gradient(circle, rgba(16,185,129,0.2) 0%, rgba(0,0,0,0.95) 70%)' : 'radial-gradient(circle, rgba(239,68,68,0.2) 0%, rgba(0,0,0,0.95) 70%)';
                icon.innerText = isWin ? '📈' : '📉';
                title.innerText = isWin ? 'TAKE PROFIT' : 'MARGIN CALL';
                title.style.color = isWin ? '#10b981' : '#ef4444';
                title.style.textShadow = 'none';
                desc.innerText = isWin ? 'Сделка закрыта в плюс. Банк твой!' : 'Ликвидация. Рынок оказался сильнее.';
                amount.innerText = isWin ? `+ ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB` : `- ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB`;
                amount.style.color = isWin ? '#10b981' : '#ef4444';
                btnShare.style.display = isWin ? 'block' : 'none';
                btnExit.innerText = isWin ? 'Зафиксировать прибыль' : 'Покинуть биржу';
            } 
            else if (currentArenaTheme === 'cyber') {
                resScreen.style.background = isWin ? 'radial-gradient(circle, rgba(251,191,36,0.3) 0%, rgba(0,0,0,0.95) 80%)' : 'rgba(10,0,0,0.95)';
                icon.innerText = isWin ? '💥' : '☠️';
                title.innerText = isWin ? 'FATALITY' : 'WASTED';
                title.style.color = isWin ? '#fbbf24' : '#ef4444';
                title.style.textShadow = isWin ? '0 0 20px #fbbf24' : '0 0 20px #ef4444';
                desc.innerText = isWin ? 'Противник стерт в пиксели.' : 'Критический сбой системы.';
                amount.innerText = isWin ? `+ ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB` : `- ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB`;
                amount.style.color = isWin ? '#fbbf24' : '#ef4444';
                btnShare.style.display = isWin ? 'block' : 'none';
                btnExit.innerText = isWin ? 'Покинуть Арену' : 'Отключиться';
            }
            tg.HapticFeedback.notificationOccurred(isWin ? 'success' : 'error');
        }

        function closePvPResult(share) {
            document.getElementById('pvpResultScreen').style.display = 'none';
            if(share) {
                shareResult(`⚔️ Я разнес оппонента на Арене и забрал ${lastPvPWinAmount.toLocaleString('ru-RU')} $ROB! Хватит смелости бросить мне вызов? Ссылка в профиле.`);
            }
        }

        tapBtn.addEventListener('click', (e) => {
            if (!isRocketActive) { if (energy <= 0) { showToast(currentLang === 'en' ? "⚡ No energy!" : "⚡ Энергия на нулю!"); return; } energy--; updateEnergyVisual(); }
            if (isRocketActive) { pendingRocketClicks += 1; }
            else { pendingStandardClicks += 1; }
            updateVisualScore();
            if (globalQuestClaimed !== 1) renderDailyQuestUI();

            tg.HapticFeedback.impactOccurred('medium');
            let activeArt = ARTIFACTS.find(a => a.id === currentArtifactId) || ARTIFACTS[0];
            let earnAmount = isRocketActive ? (multitapLevel + activeArt.bonus) * 5 : (multitapLevel + activeArt.bonus);
            const rect = tapBtn.getBoundingClientRect();
            const hasPointerCoordinates = e.clientX !== 0 || e.clientY !== 0;
            const x = hasPointerCoordinates ? e.clientX : rect.left + rect.width / 2;
            const y = hasPointerCoordinates ? e.clientY : rect.top + rect.height / 2;
            const rotateY = ((x - rect.left) / rect.width - 0.5) * 14;
            const rotateX = ((rect.top + rect.height / 2 - y) / rect.height) * 14;

            clearTimeout(tapBtn.tiltResetTimer);
            clearTimeout(tapBtn.tiltCleanupTimer);
            tapBtn.classList.remove('tilt-return');
            tapBtn.classList.add('tilt-effect');
            tapBtn.style.transform = `perspective(700px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale(0.96)`;
            tapBtn.tiltResetTimer = setTimeout(() => {
                tapBtn.classList.add('tilt-return');
                tapBtn.style.transform = 'perspective(700px) rotateX(0deg) rotateY(0deg) scale(1)';
                tapBtn.tiltCleanupTimer = setTimeout(() => {
                    tapBtn.style.transform = '';
                    tapBtn.classList.remove('tilt-effect', 'tilt-return');
                }, 280);
            }, 90);

            showFloatingEffects(x, y, earnAmount, isRocketActive);
        });

        function syncWithServer(isInitial = false) {
            let stdToSend = pendingStandardClicks; let rktToSend = pendingRocketClicks;
            inFlightStandardClicks += stdToSend; inFlightRocketClicks += rktToSend;
            pendingStandardClicks = 0; pendingRocketClicks = 0;
            
            fetch(`${BACKEND_URL}/sync`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initData: tg.initData, standard_clicks: stdToSend, rocket_clicks: rktToSend, currentArtifactId }) })
            .then(res => res.json()).then(data => {
                if (data.status === "success") {
                    serverTaps = data.new_taps_balance; serverBonus = data.new_bonus_balance;
                    if (data.current_squad) currentMySquad = data.current_squad;
                    globalDailyStreak = data.daily_streak || 0; globalLastClaimDate = data.last_claim_date || "";
                    try { globalClaimedSponsors = JSON.parse(data.claimed_sponsors || "[]"); } catch(e) { globalClaimedSponsors = []; }
                    globalDailyTaps = data.daily_taps || 0; globalQuestClaimed = data.daily_quest_claimed || 0;
                    
                    inFlightStandardClicks = Math.max(0, inFlightStandardClicks - stdToSend);
                    inFlightRocketClicks = Math.max(0, inFlightRocketClicks - rktToSend);
                    
                    renderDailyRewardUI(); renderDailyQuestUI(); renderSponsorsUI();

                    if (data.rockets_left !== undefined) {
                        rocketsLeft = data.rockets_left; 
                        maxRockets = data.max_rockets !== undefined ? data.max_rockets : maxRockets;
                        document.getElementById('rocketCount').innerText = `${rocketsLeft}/${maxRockets}`;
                        
                        let btn = document.getElementById('btnActivateRocket');
                        if (rocketsLeft <= 0) { btn.innerText = currentLang === 'en' ? "Finished ❌" : "Закончились ❌"; btn.style.background = "var(--panel-border)"; btn.disabled = true; }
                        else if (!isRocketActive) { btn.innerText = currentLang === 'en' ? "Launch Rocket 🚀" : "Запустить Ракету 🚀"; btn.style.background = "linear-gradient(90deg, #ef4444, #f59e0b)"; btn.disabled = false; }
                    }
                    if (data.turbine_charges !== undefined) {
                        currentTurbineCharges = data.turbine_charges; maxTurbineCharges = data.max_charges;
                        document.getElementById('turbineChargesUI').innerText = `${currentTurbineCharges}/${maxTurbineCharges}`;
                    }
                    if (data.owned_arena_themes !== undefined) {
                        ownedArenaThemes = data.owned_arena_themes;
                        if (!ownedArenaThemes.includes(currentArenaTheme)) currentArenaTheme = 'meme';
                        renderArenaStyles();
                    }
                    updateVisualScore();
                    if (isInitial && data.earned_offline > 0) { document.getElementById('offlineRewardAmount').innerText = data.earned_offline.toLocaleString('ru-RU'); document.getElementById('offlineModal').style.display = 'flex'; }
                } else {
                    pendingStandardClicks += stdToSend; pendingRocketClicks += rktToSend; 
                    inFlightStandardClicks = Math.max(0, inFlightStandardClicks - stdToSend); inFlightRocketClicks = Math.max(0, inFlightRocketClicks - rktToSend);
                    updateVisualScore();
                }
            }).catch(() => { 
                pendingStandardClicks += stdToSend; pendingRocketClicks += rktToSend; 
                inFlightStandardClicks = Math.max(0, inFlightStandardClicks - stdToSend); inFlightRocketClicks = Math.max(0, inFlightRocketClicks - rktToSend);
                updateVisualScore();
            });
        }

        setInterval(() => { syncWithServer(false); }, 3000); 

        window.addEventListener('visibilitychange', () => { 
            let totalStd = pendingStandardClicks + inFlightStandardClicks; let totalRkt = pendingRocketClicks + inFlightRocketClicks;
            if (document.visibilityState === 'hidden' && (totalStd > 0 || totalRkt > 0)) { 
                navigator.sendBeacon(`${BACKEND_URL}/sync`, JSON.stringify({ initData: tg.initData, standard_clicks: totalStd, rocket_clicks: totalRkt, currentArtifactId })); 
                pendingStandardClicks = 0; pendingRocketClicks = 0; inFlightStandardClicks = 0; inFlightRocketClicks = 0;
            } 
        });
