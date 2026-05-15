// Package views provides the Ops tab for the Bubble Tea TUI.
// BUILD.md Task 5.5.
package views

import (
	"fmt"
	"strings"

	"github.com/akulasaivineeth/Career-ops-autonomus/dashboard/internal/data"
)

// OpsView renders the Ops tab content as a plain string (Bubble Tea / Lipgloss
// styling can be layered on top when the full TUI is wired in).
func OpsView(summary data.AuditSummary) string {
	var b strings.Builder

	b.WriteString("── Ops ─────────────────────────────────────────────────────\n\n")

	// Today
	b.WriteString(fmt.Sprintf(
		"  Today:   %d applied   %d submitted   %d failed\n",
		summary.TodayTotal, summary.TodaySubmit, summary.TodayFailed,
	))
	if summary.TotalAllTime > 0 {
		rate := float64(summary.TodaySubmit) / float64(summary.TodayTotal) * 100
		b.WriteString(fmt.Sprintf("  Rate:    %.1f%% today  |  %d total all-time\n", rate, summary.TotalAllTime))
	}

	// Pending approvals
	if summary.PendingGates > 0 {
		b.WriteString(fmt.Sprintf("\n  ⏳ %d gate(s) awaiting your approval\n", summary.PendingGates))
	}

	// By ATS
	if len(summary.ByATSFamily) > 0 {
		b.WriteString("\n  Submitted by ATS:\n")
		for ats, n := range summary.ByATSFamily {
			b.WriteString(fmt.Sprintf("    %-16s %d\n", ats, n))
		}
	}

	// By status
	if len(summary.ByStatus) > 0 {
		b.WriteString("\n  All runs by status:\n")
		for status, n := range summary.ByStatus {
			b.WriteString(fmt.Sprintf("    %-22s %d\n", status, n))
		}
	}

	b.WriteString("\n  Bridge: http://127.0.0.1:8765  Dashboard: http://127.0.0.1:8765/\n")
	return b.String()
}

// OpsViewFromDB is a convenience wrapper that loads data then renders.
func OpsViewFromDB() string {
	summary, err := data.LoadAuditSummary()
	if err != nil {
		return fmt.Sprintf("Ops: error loading DB — %v\n", err)
	}
	return OpsView(summary)
}
