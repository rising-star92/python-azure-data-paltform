# Databricks notebook source
from os import environ

configs = {
  "fs.azure.account.auth.type": "CustomAccessToken",
  "fs.azure.account.custom.token.provider.class": spark.conf.get("spark.databricks.passthrough.adls.gen2.tokenProviderClassName")
}
known_mounts = [mount.mountPoint for mount in dbutils.fs.mounts()]
for container in ["models", "orchestration", "snapshots", "source", "utilities"]:
    if f"/mnt/{container}" in known_mounts:
        continue
    dbutils.fs.mount(
        source=f"abfss://{container}@{environ['DATA_LAKE_NAME']}.dfs.core.windows.net/",
        mount_point=f"/mnt/{container}",
        extra_configs=configs)
