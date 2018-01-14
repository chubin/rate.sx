
/*
This file cotains helper functions,
that used to convert data from string type,
that was used initially, to float and int types
that is used now.

You don't need this script anymore, 
because the data have correct types
*/

db.coins.find().forEach(function (x) {
  x.rank = parseInt(x.rank);
  x.available_supply = parseInt(x.available_supply);
  x.total_supply = parseInt(x.total_supply);
  x.last_updated = parseInt(x.last_updated);

  x.price_usd = parseFloat(x.price_usd);
  x["24h_volume_usd"] = parseFloat(x["24h_volume_usd"]);
  x.market_cap_usd = parseFloat(x.market_cap_usd);

  db.coins.save(x);

});

db.currencies.find().forEach(function (x) {

  x.last_updated = parseInt(x.last_updated);
  db.currencies.save(x);

});

db.marketcap.find().forEach(function (x) {
  x.active_currencies = parseInt(x.active_currencies);
  x.active_assets = parseInt(x.active_assets);
  x.active_markets = parseInt(x.active_markets);
  x.last_updated = parseInt(x.last_updated);
  x.timestamp = parseInt(x.timestamp);

  x.total_market_cap_usd = parseFloat(x.total_market_cap_usd);
  x.total_24h_volume_usd = parseFloat(x.total_24h_volume_usd);
  x.bitcoin_percentage_of_market_cap = parseFloat(x.bitcoin_percentage_of_market_cap);

  db.marketcap.save(x);

});
