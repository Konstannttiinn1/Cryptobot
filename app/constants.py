from dataclasses import dataclass


@dataclass(frozen=True)
class Coin:
    coin_id: str
    symbol: str
    name: str
    emoji: str = "🪙"
    market_cap_rank: int = 0


AVAILABLE_COINS: tuple[Coin, ...] = (
    Coin("bitcoin", "BTC", "Bitcoin", "₿", 1),
    Coin("ethereum", "ETH", "Ethereum", "♦️", 2),
    Coin("the-open-network", "TON", "Gram", "🔵", 3),
    Coin("tether", "USDT", "Tether", "💵", 4),
    Coin("binancecoin", "BNB", "BNB", "🟡", 5),
    Coin("solana", "SOL", "Solana", "🟣", 6),
    Coin("ripple", "XRP", "XRP", "✖️", 7),
    Coin("dogecoin", "DOGE", "Dogecoin", "🐶", 8),
    Coin("tron", "TRX", "Tron", "🔺", 9),
    Coin("notcoin", "NOT", "Notcoin", "🎮", 10),
    Coin("usd-coin", "USDC", "USDC", "💵", 11),
    Coin("staked-ether", "STETH", "Lido Staked Ether", "♦️", 12),
    Coin("cardano", "ADA", "Cardano", "🔷", 13),
    Coin("avalanche-2", "AVAX", "Avalanche", "🔺", 14),
    Coin("shiba-inu", "SHIB", "Shiba Inu", "🐕", 15),
    Coin("wrapped-bitcoin", "WBTC", "Wrapped Bitcoin", "₿", 16),
    Coin("chainlink", "LINK", "Chainlink", "🔗", 17),
    Coin("bitcoin-cash", "BCH", "Bitcoin Cash", "₿", 18),
    Coin("polkadot", "DOT", "Polkadot", "⚫", 19),
    Coin("leo-token", "LEO", "LEO Token", "🪙", 20),
    Coin("litecoin", "LTC", "Litecoin", "Ł", 21),
    Coin("near", "NEAR", "NEAR Protocol", "🪙", 22),
    Coin("uniswap", "UNI", "Uniswap", "🦄", 23),
    Coin("dai", "DAI", "Dai", "💵", 24),
    Coin("internet-computer", "ICP", "Internet Computer", "∞", 25),
    Coin("aptos", "APT", "Aptos", "🪙", 26),
    Coin("ethereum-classic", "ETC", "Ethereum Classic", "♦️", 27),
    Coin("pepe", "PEPE", "Pepe", "🐸", 28),
    Coin("kaspa", "KAS", "Kaspa", "🪙", 29),
    Coin("first-digital-usd", "FDUSD", "First Digital USD", "💵", 30),
    Coin("stellar", "XLM", "Stellar", "⭐", 31),
    Coin("crypto-com-chain", "CRO", "Cronos", "🪙", 32),
    Coin("render-token", "RENDER", "Render", "🎨", 33),
    Coin("mantle", "MNT", "Mantle", "🪙", 34),
    Coin("hedera-hashgraph", "HBAR", "Hedera", "🪙", 35),
    Coin("filecoin", "FIL", "Filecoin", "📁", 36),
    Coin("cosmos", "ATOM", "Cosmos Hub", "⚛️", 37),
    Coin("okb", "OKB", "OKB", "🪙", 38),
    Coin("arbitrum", "ARB", "Arbitrum", "🔵", 39),
    Coin("vechain", "VET", "VeChain", "✅", 40),
    Coin("maker", "MKR", "Maker", "🪙", 41),
    Coin("immutable-x", "IMX", "Immutable", "🎮", 42),
    Coin("optimism", "OP", "Optimism", "🔴", 43),
    Coin("injective-protocol", "INJ", "Injective", "🪙", 44),
    Coin("sui", "SUI", "Sui", "💧", 45),
    Coin("bittensor", "TAO", "Bittensor", "🧠", 46),
    Coin("the-graph", "GRT", "The Graph", "📊", 47),
    Coin("theta-token", "THETA", "Theta Network", "θ", 48),
    Coin("fantom", "FTM", "Fantom", "👻", 49),
    Coin("thorchain", "RUNE", "THORChain", "ᚱ", 50),
    Coin("algorand", "ALGO", "Algorand", "🪙", 51),
    Coin("lido-dao", "LDO", "Lido DAO", "🪙", 52),
    Coin("aave", "AAVE", "Aave", "👻", 53),
    Coin("flow", "FLOW", "Flow", "🌊", 54),
    Coin("gala", "GALA", "GALA", "🎮", 55),
    Coin("jupiter-exchange-solana", "JUP", "Jupiter", "🪐", 56),
    Coin("quant-network", "QNT", "Quant", "🪙", 57),
    Coin("celestia", "TIA", "Celestia", "🪐", 58),
    Coin("bonk", "BONK", "Bonk", "🐶", 59),
    Coin("sei-network", "SEI", "Sei", "🪙", 60),
    Coin("flare-networks", "FLR", "Flare", "🔥", 61),
    Coin("eos", "EOS", "EOS", "🪙", 62),
    Coin("multiversx", "EGLD", "MultiversX", "🪙", 63),
    Coin("axie-infinity", "AXS", "Axie Infinity", "🎮", 64),
    Coin("tezos", "XTZ", "Tezos", "🪙", 65),
    Coin("mina-protocol", "MINA", "Mina Protocol", "🪙", 66),
    Coin("the-sandbox", "SAND", "The Sandbox", "🏝️", 67),
    Coin("decentraland", "MANA", "Decentraland", "🏙️", 68),
    Coin("kucoin-shares", "KCS", "KuCoin", "🪙", 69),
    Coin("chiliz", "CHZ", "Chiliz", "🌶️", 70),
    Coin("ecash", "XEC", "eCash", "💵", 71),
    Coin("neo", "NEO", "NEO", "🪙", 72),
    Coin("akash-network", "AKT", "Akash Network", "☁️", 73),
    Coin("dydx-chain", "DYDX", "dYdX", "🪙", 74),
    Coin("pendle", "PENDLE", "Pendle", "🪙", 75),
    Coin("frax", "FRAX", "Frax", "💵", 76),
    Coin("pyth-network", "PYTH", "Pyth Network", "🐍", 77),
    Coin("iota", "IOTA", "IOTA", "🪙", 78),
    Coin("synthetix-network-token", "SNX", "Synthetix", "🪙", 79),
    Coin("curve-dao-token", "CRV", "Curve DAO", "🪙", 80),
    Coin("rocket-pool-eth", "RETH", "Rocket Pool ETH", "🚀", 81),
    Coin("rocket-pool", "RPL", "Rocket Pool", "🚀", 82),
    Coin("pancakeswap-token", "CAKE", "PancakeSwap", "🥞", 83),
    Coin("trust-wallet-token", "TWT", "Trust Wallet", "🛡️", 84),
    Coin("zcash", "ZEC", "Zcash", "🛡️", 85),
    Coin("havven", "SNX", "Synthetix Network", "🪙", 86),
    Coin("compound-governance-token", "COMP", "Compound", "🪙", 87),
    Coin("1inch", "1INCH", "1inch", "🪙", 88),
    Coin("enjincoin", "ENJ", "Enjin Coin", "🎮", 89),
    Coin("basic-attention-token", "BAT", "Basic Attention", "🦇", 90),
    Coin("dash", "DASH", "Dash", "🪙", 91),
    Coin("kava", "KAVA", "Kava", "🪙", 92),
    Coin("zilliqa", "ZIL", "Zilliqa", "🪙", 93),
    Coin("gnosis", "GNO", "Gnosis", "🪙", 94),
    Coin("blur", "BLUR", "Blur", "🖼️", 95),
    Coin("oasis-network", "ROSE", "Oasis", "🌹", 96),
    Coin("wemix-token", "WEMIX", "WEMIX", "🎮", 97),
    Coin("convex-finance", "CVX", "Convex Finance", "🪙", 98),
    Coin("kusama", "KSM", "Kusama", "🐦", 99),
    Coin("ankr", "ANKR", "Ankr Network", "⚓", 100),
)

COINS_BY_ID = {coin.coin_id: coin for coin in AVAILABLE_COINS}
DEFAULT_COIN_IDS = ("bitcoin", "the-open-network", "tether")
SUPPORTED_CURRENCIES = ("rub", "usd")
SUPPORTED_INTERVALS = (5, 10, 15, 30, 60)
MAX_SELECTED_COINS = 20
COINS_PER_PAGE = 10
MAX_SEARCH_RESULTS = 10
MAX_MESSAGE_LENGTH = 3900
TRUNCATED_MESSAGE_NOTICE = "Часть монет не показана из-за ограничения длины сообщения."
