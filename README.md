# Trading-bot-dydx
A trading bot that works with the dydx API

1. To use this bot you need to have a wallet that is compatible with dydx like [Metamask](https://chrome.google.com/webstore/detail/metamask/nkbihfbeogaeaoehlefnkodbefgpgknn?hl=fr "Metamask")

2. You need to connect your wallet to [dydx](https://dydx.exchange/r/EBZQEZSQ "dydx")

3. You need to deposit a minimal of $200 or the size of your position may be too low and make the bot crashed

4. Clone the repository

```
git clone git@github.com:1NainConnu34/Trading-bot-dydx.git
```
5. Install libraries :

```
pip install dydx-v3-python
pip install pandas
```

6. Get your API key, secret key, passphrase and stark private key by following those steps :

- From the dydx Perpetuals exchange, right-click anywhere on your web browser, and select Inspect to open Developer Tools
- Go to Application > Local Storage > https://trade.dydx.exchange
- Select STARK_KEY_PAIRS and click the drop-down next to your wallet address to get the stark private key
- Select API_KEY_PAIRS and click the drop-down next to your wallet address to get the API key, secret key, and passphrase

7. Now put your Ethereum address, API key, secret key, passphrase and stark private key in the script where it is indicated

8. You can now run the bot
