# Carmille

## Purpose

A Slack application that lets you request a time-bound archive of a particular public channel. To use, invite the bot user into a public channel, then type `/carmille` to begin the 

## Name

[René Carmille](https://en.wikipedia.org/wiki/Ren%C3%A9_Carmille). A good hacker.

## Setup

### S3 Storage

You're going to need an S3-compatible storage environment to store the archives. It needs to be configured to make public URLs for any given object put into the bucket, as Carmille will pass those to users.

#### Removing Old Archives

The script at <cron/remove-old.sh> looks for an `s3cmd` install and config file (you can specify the path), and uses a bucket name of `carmille` by default; it searches for files older than 1 hour and deletes them. I run it hourly, via cron. You can (and should) use a separate access key and secret from the one you're providing to the container for normal use.

### How to Set Up At Slack

Create a new app! It needs these permissions:

* `channels:history`
* `channels:read`
* `commands`
* `emoji:read`
* `reactions:read`
* `users:read`

You need to set up the following things:
* Enable (under Developer Beta features) the time picker element.
* Under Interactivity & Shortcuts, set the Request URL to https://YOUR_CARMILLE_DOMAIN.com/slack/events .
* Under Slack Commands, set `/carmille` to use the URL https://YOUR_CARMILLE_DOMAIN.com/slack/events . The Description is "Download Channel Archive."
* Under OAuth & Permissions, set up a redirect URL of https://YOUR_CARMILLE_DOMAIN.com/slack/oauth_redirect .

Optionally, set the look for your app in the Display Information section of the Basic Information page. I think #960018 is a pretty color.

To install on your workspace, go to <https://YOUR_CARMILLE_DOMAIN.com/slack/install> and click the Add to Slack button.

## How to Run the Bot

### Environment Variables

There are five actual secrets, and three configuration values, that the app needs from its environment. Here they are.

* `S3_API_ENDPOINT`: API endpoint for S3 actions. If using Linode Object Storage, us-east-1.linodeobjects.com .
* `S3_BUCKET`: Bucket name for S3 actions.
* `S3_ACCESS_KEY`: Access key for S3 actions.
* `S3_SECRET_KEY`: Secret key for S3 actions.
* `S3_WEBSITE_PREFIX`: The prefix (including https://) for URLs to pass to end users; the prefix should be such that the bot can return `<prefix>/<nameoffile.zip>` and that'll work for the user.
* `SLACK_CLIENT_ID`: The client ID from the Slack app.
* `SLACK_CLIENT_SECRET`: The client secret from the Slack app.
* `SLACK_SIGNING_SECRET`: The signing secret from the Slack app.

### Run Using Docker

```
mkdir -p oauthdata
docker run -d --rm \
    -e S3_API_ENDPOINT=us-east-1.linodeobjects.com \
    -e S3_BUCKET=carmilleForYou \
    -e S3_ACCESS_KEY=AccessKey \
    -e S3_SECRET_KEY=SecretKey \
    -e S3_WEBSITE_PREFIX=https://example.com \
    -e SLACK_CLIENT_ID=nothing-to-see-here \
    -e SLACK_CLIENT_SECRET=nothing-to-see-here \
    -e SLACK_SIGNING_SECRET=s3kr1t \
    -v $(pwd)/oauthdata:/root/src/data \
    -p 8000:8000 \
    ghcr.io/ussjoin/carmille:latest
```

Note that this daemonizes into the background (`-d`) and destroys itself on termination (`-rm`). You might want to use `-d --restart=always` instead, but you do you.

The docker image is automatically built on every push to the main branch, and stored in the GitHub Container Registry. See <https://github.com/ussjoin/carmille/actions> for information on when it was last built. If you need it for another processor type, `docker build .` works just perfectly, as does the standard `docker buildx` cross-compilation.

### Run Without Docker

```
mkdir -p tmp # Used for archive prep
mkdir -p data # Used for persistent OAuth data store
export S3_API_ENDPOINT=us-east-1.linodeobjects.com
export S3_BUCKET=carmilleForYou
export S3_ACCESS_KEY=AccessKey
export S3_SECRET_KEY=SecretKey
export S3_WEBSITE_PREFIX=https://example.com
export SLACK_CLIENT_ID=nothing-to-see-here
export SLACK_CLIENT_SECRET=nothing-to-see-here
export SLACK_SIGNING_SECRET=s3kr1t

python3 main.py
```

### Nginx Proxy

You'll want to set up an Nginx proxy on the machine that's hosting your Docker (or non-Docker) install of Carmille. If you're using Certbot / Let's Encrypt for TLS, generally follow the instructions at <https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/>. Your starting (port 80) listener can be like

```
server {
  listen 80 default_server;
  listen [::]:80 default_server;
  server_name YOUR_CARMILLE_DOMAIN.com;
  location / {
    proxy_pass http://localhost:8000;
  }
}
```

Then just follow the instructions and Certbot will modify your Nginx config as it runs.
