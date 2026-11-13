#!/usr/bin/env bash
# Put one CPU core of a Linux machine into a reproducible benchmark mode:
#   - turbo / boost disabled (globally),
#   - "performance" governor on the core,
#   - core frequency fixed (min = max) to a fraction (default 85%) of the
#     nominal, non-boosted maximum frequency,
#   - energy-performance preference "performance" (Intel HWP / amd-pstate EPP).
# The previous settings are saved and can be restored.
#
# Usage (root required):
#   sudo scripts/cpu_benchmark_mode.sh setup <core> [fraction]
#   ocp-benchmark run -c <config.json> --cpu-core <core> --repeat-times 10
#   sudo scripts/cpu_benchmark_mode.sh restore
#   scripts/cpu_benchmark_mode.sh status <core>
#
# Supported cpufreq drivers: intel_pstate, intel_cpufreq, amd-pstate(-epp),
# acpi-cpufreq. For best results also keep the hyperthread sibling of <core>
# idle (or boot with isolcpus=<core> nohz_full=<core>).

set -euo pipefail

# Overridable for testing against a fake sysfs tree (CPU_BENCH_TEST=1 also
# skips the Linux/root checks).
STATE_FILE=${CPU_BENCH_STATE_FILE:-/var/tmp/ocp_qp_benchmark_cpu_state}
SYS=${CPU_BENCH_SYSFS:-/sys/devices/system/cpu}
TEST_MODE=${CPU_BENCH_TEST:-0}

die() { echo "error: $*" >&2; exit 1; }

require_linux() {
    [[ "$TEST_MODE" == 1 || "$(uname -s)" == "Linux" ]] || die "only supported on Linux."
}

require_root() {
    [[ "$TEST_MODE" == 1 || "$(id -u)" -eq 0 ]] || die "run as root (sudo)."
}

cpufreq_dir() {
    local core=$1
    local dir="$SYS/cpu$core/cpufreq"
    [[ -d "$dir" ]] || die "no cpufreq interface for core $core ($dir)."
    echo "$dir"
}

# Global turbo/boost switch: prints "<path> <value meaning disabled>".
turbo_switch() {
    if [[ -w "$SYS/intel_pstate/no_turbo" ]]; then
        echo "$SYS/intel_pstate/no_turbo 1"
    elif [[ -w "$SYS/cpufreq/boost" ]]; then
        echo "$SYS/cpufreq/boost 0"
    fi
}

# Nominal (non-boosted) maximum frequency of the core in kHz.
nominal_freq_khz() {
    local dir=$1
    if [[ -r "$dir/base_frequency" ]]; then                # intel_pstate
        cat "$dir/base_frequency"
    elif [[ -r "$dir/amd_pstate_nominal_freq" ]]; then     # amd-pstate
        cat "$dir/amd_pstate_nominal_freq"
    else                                                   # acpi-cpufreq: boost
        cat "$dir/cpuinfo_max_freq"                        # P-states not listed
    fi
}

save() {  # append "<path> <current value>" to the state file
    local path=$1
    [[ -e "$path" ]] && echo "$path $(cat "$path")" >> "$STATE_FILE"
    return 0
}

write() {
    local path=$1 value=$2
    echo "$value" > "$path" || die "could not write '$value' to $path."
}

setup() {
    local core=$1 fraction=${2:-0.85}
    require_root
    [[ -e "$STATE_FILE" ]] && die "$STATE_FILE exists: run 'restore' first."
    local dir; dir=$(cpufreq_dir "$core")

    # save the original settings; the order is the restore order
    # (max before min, so that the restored min never exceeds the max)
    : > "$STATE_FILE"
    save "$dir/scaling_governor"
    save "$dir/energy_performance_preference"
    save "$dir/scaling_max_freq"
    save "$dir/scaling_min_freq"
    local turbo; turbo=$(turbo_switch || true)
    [[ -n "$turbo" ]] && save "${turbo% *}"

    # 1) disable turbo / boost
    if [[ -n "$turbo" ]]; then
        write "${turbo% *}" "${turbo#* }"
    else
        echo "warning: no global turbo/boost switch found; check the BIOS." >&2
    fi

    # 2) governor and energy-performance preference
    write "$dir/scaling_governor" performance
    if [[ -w "$dir/energy_performance_preference" ]]; then
        write "$dir/energy_performance_preference" performance
    fi

    # 3) fixed frequency: fraction of the nominal maximum
    local nominal min_hw target
    nominal=$(nominal_freq_khz "$dir")
    min_hw=$(cat "$dir/cpuinfo_min_freq")
    target=$(awk -v n="$nominal" -v f="$fraction" -v m="$min_hw" \
        'BEGIN { t = int(n * f); if (t < m) t = m; print t }')
    write "$dir/scaling_min_freq" "$min_hw"   # lower min first: min <= max always
    write "$dir/scaling_max_freq" "$target"
    write "$dir/scaling_min_freq" "$target"

    echo "core $core: driver $(cat "$dir/scaling_driver"), turbo off, governor performance"
    echo "core $core: nominal max $((nominal / 1000)) MHz, target ${fraction} x nominal = $((target / 1000)) MHz"
    [[ "$TEST_MODE" == 1 ]] || sleep 0.5
    status "$core"
}

restore() {
    require_root
    [[ -e "$STATE_FILE" ]] || die "no saved state ($STATE_FILE)."
    while read -r path value; do
        echo "$value" > "$path" 2>/dev/null || echo "warning: could not restore $path" >&2
    done < "$STATE_FILE"
    rm -f "$STATE_FILE"
    echo "CPU settings restored."
}

status() {
    local core=$1
    local dir; dir=$(cpufreq_dir "$core")
    local turbo; turbo=$(turbo_switch || true)
    echo "core $core: driver=$(cat "$dir/scaling_driver") governor=$(cat "$dir/scaling_governor")" \
         "min=$(($(cat "$dir/scaling_min_freq") / 1000))MHz max=$(($(cat "$dir/scaling_max_freq") / 1000))MHz" \
         "cur=$(($(cat "$dir/scaling_cur_freq") / 1000))MHz" \
         "${turbo:+turbo_switch=${turbo% *}=$(cat "${turbo% *}")}"
}

require_linux
case "${1:-}" in
    setup)   [[ $# -ge 2 ]] || die "usage: $0 setup <core> [fraction]"; setup "$2" "${3:-0.85}" ;;
    restore) restore ;;
    status)  [[ $# -ge 2 ]] || die "usage: $0 status <core>"; status "$2" ;;
    *)       die "usage: $0 {setup <core> [fraction] | restore | status <core>}" ;;
esac
