# Carmille

## Purpose

A Slack application that lets you request a time-bound archive of a particular public channel.

## Name

[René Carmille](https://en.wikipedia.org/wiki/Ren%C3%A9_Carmille). A good hacker.

## How to Set Up At Slack


## How to Run

### Environment Variables

There are four actual secrets, and three configuration values, that the app needs from its environment. Here they are.

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

Note that this daemonizes into the background (`-d`) and destroys itself on termination (`-rm`). You might want to use `-d --restart` instead, but you do you.

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
