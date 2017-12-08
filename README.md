
*rate.sx* — console serice for getting cryptocurrencies exchange rates

## Usage

You can access the service from a shell or from a Web browser:

To get current market capitalization (in USD) of the top ten cryptocoins in shell:

```
    curl rate.sx
```

Or if you want to get the output in some other currency,
specify it in the domain name (lower-, upper- or mixed-case):

```
    curl eur.rate.sx
```

To use it in a web browser, just type rate.sx in the location bar.

![rate.sx screenshot](http://rate.sx/files/screenshot.png)

## Features

* simple curl/browser interface
* available everywhere, no installation needed

## Supported currencies

You can find actual list of the supported currencies in `/:help`.
12 different currencies are supported at the moment.

## Disclaimer

Though *rate.sx* synchronizes with online cryptocurrencies exchanges every five minutes,
we cannot guarantee absolute accuracy of the displayed exchange rates.
You should always confirm current rates before making any transactions
that could be affected by changes in the exchange rates.
Crypocurrency rates based on the data provided by exchanges APIs.
All rates are for information purposes only and are subject to change without prior notice.
Since rates for actual transactions may vary,
we are not offering to enter into any transaction at any rate displayed.
Displayed rates are composite prices and not intended to be used for investment purposes. 

## Integration

### GNU Emacs

[rate-sx.el](https://github.com/davep/rate-sx.el) — rate.sx in Emacs (courtesy of Dave Pearson @davep)

![rate-sx.el screenshot](https://user-images.githubusercontent.com/28237/33782065-1569d88e-dc4f-11e7-9547-c9e14dcfd470.png)

## rate.sx Server Installation

If you want install the *rate.sx* server, you can do it. Keep in mind that you need some data 
datasource. Server without data is useless (of course, you can always
use rate.sx as the datasource, though the point of such strange configuration is not clear).

### Install rate.sx server

```
git clone github.com/chubin/rate.sx
cd rate.sx
virtualenv ve
ve/bin/pip install -r requirements.txt
ve/bin/python bin/srv.py

```

### Configure HTTP-frontend service

Configure the web server, that will be used to access the service (if you want to use a web frontend; it's recommended):

```
server {
    listen [::]:80;
    server_name  rate.sx *.rate.sx;
    access_log  /var/log/nginx/rate.sx-access.log  main;
    error_log  /var/log/nginx/rate.sx-error.log;

    location / {
        proxy_pass         http://127.0.0.1:8003;

        proxy_set_header   Host             $host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $remote_addr;

        client_max_body_size       10m;
        client_body_buffer_size    128k;

        proxy_connect_timeout      90;
        proxy_send_timeout         90;
        proxy_read_timeout         90;

        proxy_buffer_size          4k;
        proxy_buffers              4 32k;
        proxy_busy_buffers_size    64k;
        proxy_temp_file_write_size 64k;

        expires                    off;
    }
}
```


