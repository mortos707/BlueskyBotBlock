BEGIN TRANSACTION;
DROP TABLE IF EXISTS "B3";
CREATE TABLE IF NOT EXISTS "B3" (
	"rec_num"	INTEGER,
	"date_time"	TEXT,
	"handle"	TEXT,
	"status"	TEXT,
	"block"	TEXT,
	"mute"	TEXT,
	"active"	TEXT,
	"block_group"	TEXT,
	PRIMARY KEY("rec_num" AUTOINCREMENT)
);
COMMIT;
