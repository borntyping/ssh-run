#!/usr/bin/env python

import time

import click


with click.progressbar(range(100)) as items:
    for _ in items:
        time.sleep(0.01)
