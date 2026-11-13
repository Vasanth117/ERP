// Start a single-node replica set so later finance flows can use transactions.
const host = "mongodb:27017";

function isInitiated() {
  try {
    return rs.status().ok === 1;
  } catch (error) {
    return false;
  }
}

if (!isInitiated()) {
  rs.initiate({
    _id: "rs0",
    members: [{ _id: 0, host: host }],
  });
}

for (let attempt = 0; attempt < 40; attempt += 1) {
  try {
    const status = rs.status();
    const primary = status.members && status.members.some((member) => member.stateStr === "PRIMARY");
    if (primary) {
      quit(0);
    }
  } catch (error) {
    // Election is still in progress.
  }
  sleep(1000);
}

quit(1);
