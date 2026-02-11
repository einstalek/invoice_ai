## Deployment with fly

1. fly apps create inflow   
2. cat .env | tr '\n' ' ' | xargs flyctl secrets set
3. 
4. fly secrets set GOOGLE_OAUTH_CLIENT_SECRET_JSON="$(cat client_secret_*.json)"
5. flyctl ssh console -C "python manage.py migrate"
6. fly deploy


## Keeping the sqlite db after deleting the app

Before deleting the app (recommended):

fly volumes list
fly volumes snapshots create <volume_id>
(fly.io)

After deleting / redeploying:

Get the deleted volume ID (available for ~24 hours):
fly volumes list --all
List its snapshots:
fly volumes snapshots list <volume_id>
Create a new volume from a snapshot:
fly volumes create app_data --snapshot-id <snapshot_id> -s <size_in_gb>
Deploy the new app with the mount:
[mounts]
  source = "app_data"
  destination = "/data"
(fly.io)

Important limits:

Snapshots are kept 5 days by default; you can set retention (1–60 days) when creating a volume. (fly.io)
Once snapshots expire, you can’t restore. (fly.io)
If you want, I can add a quick backup command to dump db.sqlite3 to S3 so you’re not relying only on snapshots.