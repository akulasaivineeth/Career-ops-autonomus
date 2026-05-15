// Package data reads career-ops operational data from SQLite for the TUI.
// BUILD.md Task 5.5.
package data

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"time"

	_ "modernc.org/sqlite" // pure-Go SQLite driver (no CGo, no libsqlite3 needed in CI)
)

// Run represents one apply attempt.
type Run struct {
	RunID         string
	JdID          string
	JdURL         string
	Track         string
	Score         float64
	AtsFamily     string
	Status        string
	AutonomyLevel int
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

// AuditSummary is the aggregated ops view for the Ops tab.
type AuditSummary struct {
	TodayTotal    int
	TodaySubmit   int
	TodayFailed   int
	PendingGates  int
	TotalAllTime  int
	ByATSFamily   map[string]int
	ByStatus      map[string]int
}

func dbPath() string {
	if p := os.Getenv("CAREEROPS_DB_PATH"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, "code", "career-ops", "db", "careerops.db")
}

// LoadAuditSummary reads aggregated stats from SQLite.
// Returns empty summary (no error) when the DB does not exist yet.
func LoadAuditSummary() (AuditSummary, error) {
	path := dbPath()
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return AuditSummary{ByATSFamily: make(map[string]int), ByStatus: make(map[string]int)}, nil
	}

	db, err := sql.Open("sqlite", path+"?mode=ro")
	if err != nil {
		return AuditSummary{}, fmt.Errorf("open db: %w", err)
	}
	defer db.Close()

	summary := AuditSummary{
		ByATSFamily: make(map[string]int),
		ByStatus:    make(map[string]int),
	}

	today := time.Now().Format("2006-01-02")

	// Today's totals
	_ = db.QueryRow(
		"SELECT COUNT(*) FROM runs WHERE created_at LIKE ?", today+"%",
	).Scan(&summary.TodayTotal)
	_ = db.QueryRow(
		"SELECT COUNT(*) FROM runs WHERE status='submitted' AND created_at LIKE ?", today+"%",
	).Scan(&summary.TodaySubmit)
	_ = db.QueryRow(
		"SELECT COUNT(*) FROM runs WHERE status='apply_failed' AND created_at LIKE ?", today+"%",
	).Scan(&summary.TodayFailed)

	// Pending approvals
	_ = db.QueryRow(
		"SELECT COUNT(*) FROM approvals WHERE decision IS NULL AND sent_at IS NOT NULL",
	).Scan(&summary.PendingGates)

	// All time
	_ = db.QueryRow("SELECT COUNT(*) FROM runs").Scan(&summary.TotalAllTime)

	// By ATS family
	rows, err := db.Query(
		"SELECT COALESCE(ats_family,'unknown') as f, COUNT(*) as n FROM runs WHERE status='submitted' GROUP BY f",
	)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var f string
			var n int
			if rows.Scan(&f, &n) == nil {
				summary.ByATSFamily[f] = n
			}
		}
	}

	// By status
	rows2, err := db.Query("SELECT COALESCE(status,'unknown') as s, COUNT(*) as n FROM runs GROUP BY s")
	if err == nil {
		defer rows2.Close()
		for rows2.Next() {
			var s string
			var n int
			if rows2.Scan(&s, &n) == nil {
				summary.ByStatus[s] = n
			}
		}
	}

	return summary, nil
}

// RecentRuns returns the most recent N runs.
func RecentRuns(limit int) ([]Run, error) {
	path := dbPath()
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil, nil
	}

	db, err := sql.Open("sqlite", path+"?mode=ro")
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}
	defer db.Close()

	rows, err := db.Query(
		`SELECT run_id, COALESCE(jd_id,''), COALESCE(jd_url,''), COALESCE(track,''),
		        COALESCE(score,0), COALESCE(ats_family,''), COALESCE(status,''),
		        COALESCE(autonomy_level,0), created_at, updated_at
		 FROM runs ORDER BY created_at DESC LIMIT ?`, limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var runs []Run
	for rows.Next() {
		var r Run
		var createdStr, updatedStr string
		if err := rows.Scan(
			&r.RunID, &r.JdID, &r.JdURL, &r.Track,
			&r.Score, &r.AtsFamily, &r.Status,
			&r.AutonomyLevel, &createdStr, &updatedStr,
		); err != nil {
			continue
		}
		r.CreatedAt, _ = time.Parse("2006-01-02T15:04:05", createdStr)
		r.UpdatedAt, _ = time.Parse("2006-01-02T15:04:05", updatedStr)
		runs = append(runs, r)
	}
	return runs, nil
}
