export class MemoryDatabase {
  constructor() {
    this.rows = new Map();
  }

  async ensureSchema() {}

  async upsertDevice(device) {
    const existing = this.rows.get(device.deviceId);
    this.rows.set(device.deviceId, {
      ...existing,
      ...device,
      firstUseDate: existing?.firstUseDate ?? device.firstUseDate,
    });
  }

  async deleteDevice(deviceId) {
    this.rows.delete(deviceId);
  }

  async readInstallStats({ activeDays = 30, recentDays = 7 } = {}) {
    const rows = [...this.rows.values()];
    const tally = (pick) => {
      const counts = new Map();
      for (const row of rows) {
        const key = pick(row);
        if (key === null || key === undefined) continue;
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
      return [...counts.entries()]
        .map(([key, total]) => ({ key: String(key), total }))
        .sort((a, b) => b.total - a.total || a.key.localeCompare(b.key));
    };

    const events = new Map();
    for (const row of rows) {
      for (const [key, value] of Object.entries(row.events ?? {})) {
        if (typeof value !== "number" || value <= 0) continue;
        const entry = events.get(key) ?? { key, total: 0, devices: 0 };
        entry.total += value;
        entry.devices += 1;
        events.set(key, entry);
      }
    }

    const positive = (row, field) => typeof row.featureUsage?.[field] === "number" && row.featureUsage[field] > 0;
    return {
      window: { activeDays, recentDays },
      totals: {
        installs: rows.length,
        activeRecent: rows.length,
        activeWindow: rows.length,
        newWindow: rows.length,
        countries: new Set(rows.map((row) => row.country).filter(Boolean)).size,
        wordsTotal: rows.reduce((sum, row) => sum + (row.wordsTotal ?? 0), 0),
        minutesSaved: rows.reduce((sum, row) => sum + (row.minutesSaved ?? 0), 0),
      },
      versions: tally((row) => row.appVersion ?? "unknown"),
      countries: tally((row) => row.country),
      features: {
        cleanupEnabled: rows.filter((row) => row.featureUsage?.cleanupEnabled === true).length,
        usesSnippets: rows.filter((row) => positive(row, "snippetsCount")).length,
        usesDictionary: rows.filter((row) => positive(row, "dictionaryCount")).length,
        hasKnowMeProfile: rows.filter((row) => row.featureUsage?.hasKnowMeProfile === true).length,
      },
      events: [...events.values()].sort((a, b) => b.total - a.total || a.key.localeCompare(b.key)),
    };
  }

  async readLeaderboard(deviceId, limit) {
    const ordered = [...this.rows.values()].sort((a, b) =>
      b.minutesSaved - a.minutesSaved || a.deviceId.localeCompare(b.deviceId)
    );
    let previousMinutes = null;
    let previousRank = 0;
    const ranked = ordered.map((row, index) => {
      const rank = row.minutesSaved === previousMinutes ? previousRank : index + 1;
      previousMinutes = row.minutesSaved;
      previousRank = rank;
      return { ...row, rank };
    });
    return {
      top: ranked.slice(0, limit),
      you: deviceId ? ranked.find((row) => row.deviceId === deviceId) ?? null : null,
    };
  }
}
