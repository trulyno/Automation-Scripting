#!/bin/bash

# Disk Space Usage Monitor
# Usage: ./disk_usage.sh <directory_path> <max_volume_mb> [threshold_percent]

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
    echo -e "${BLUE}Usage:${NC} $0 <directory_path> <max_volume_mb> [threshold_percent]"
    echo -e "  ${YELLOW}directory_path${NC}    - Path to the directory to monitor"
    echo -e "  ${YELLOW}max_volume_mb${NC}     - Maximum volume reserved for directory in MB"
    echo -e "  ${YELLOW}threshold_percent${NC} - Threshold for disk usage warning (default: 80%)"
    exit 1
}

# Function to send email notification
send_notification() {
    local usage_percent=$1
    local directory=$2
    local email="admin@example.com" 
    
    local subject="ALERT: Disk Usage Threshold Exceeded"
    local message="Directory: $directory\nCurrent Usage: $usage_percent%\nThreshold Exceeded!"
    
    # Using mail command (requires mailutils package or alternatives like s-nail)
    echo -e "$message" | mail -s "$subject" "$email" 2>/dev/null || {
        echo -e "${RED}Warning:${NC} Could not send email notification (mail command not available)"
    }
}

# Function to log disk usage
log_usage() {
    local usage_percent=$1
    local directory=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] Directory: $directory | Usage: $usage_percent%" >> disk_usage.log
}

# Function to calculate disk usage percentage
calculate_usage() {
    local directory=$1
    local max_volume_mb=$2
    
    # Get directory size in MB
    local dir_size_mb=$(du -sm "$directory" 2>/dev/null | cut -f1)
    
    if [ -z "$dir_size_mb" ]; then
        echo -e "${RED}Error:${NC} Could not calculate directory size"
        exit 1
    fi
    
    # Calculate usage percentage
    local usage_percent=$((dir_size_mb * 100 / max_volume_mb))
    
    echo "$usage_percent"
}

# Main script execution
main() {
    # Check argument count
    if [ $# -lt 2 ] || [ $# -gt 3 ]; then
        echo -e "${RED}Error:${NC} Invalid number of arguments"
        show_usage
    fi
    
    local directory="$1"
    local max_volume_mb="$2"
    local threshold_percent="${3:-80}"  # Default to 80% if not provided
    
    # Validate arguments
    if ! [[ "$max_volume_mb" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error:${NC} Maximum volume must be a positive integer"
        exit 1
    fi
    
    if ! [[ "$threshold_percent" =~ ^[0-9]+$ ]] || [ "$threshold_percent" -lt 1 ] || [ "$threshold_percent" -gt 100 ]; then
        echo -e "${RED}Error:${NC} Threshold must be a number between 1 and 100"
        exit 1
    fi
    
    # Check if directory exists
    if [ ! -d "$directory" ]; then
        echo -e "${RED}Error:${NC} Directory '$directory' does not exist"
        exit 1
    fi
    
    # Check if directory is accessible
    if [ ! -r "$directory" ]; then
        echo -e "${RED}Error:${NC} Directory '$directory' is not readable"
        exit 1
    fi
    
    # Calculate current usage
    local usage_percent=$(calculate_usage "$directory" "$max_volume_mb")
    
    # Display current status
    echo -e "\n${BLUE}┌─────────────────────────────┐${NC}"
    echo -e "${BLUE}│${NC}      ${YELLOW}Disk Usage Monitor${NC}     ${BLUE}│${NC}"
    echo -e "${BLUE}└─────────────────────────────┘${NC}"
    echo -e "Directory: ${YELLOW}$directory${NC}"
    echo -e "Max Volume: ${YELLOW}${max_volume_mb}MB${NC}"
    echo -e "Threshold: ${YELLOW}${threshold_percent}%${NC}"
    
    if [ "$usage_percent" -gt "$threshold_percent" ]; then
        echo -e "Current Usage: ${RED}${usage_percent}%${NC} ${RED}⚠ EXCEEDED${NC}"
        send_notification "$usage_percent" "$directory"
        echo -e "${YELLOW}→${NC} Email notification sent"
    else
        echo -e "Current Usage: ${GREEN}${usage_percent}%${NC} ${GREEN}✓ OK${NC}"
    fi
    
    # Log the usage
    log_usage "$usage_percent" "$directory"
    echo -e "${YELLOW}→${NC} Usage logged to disk_usage.log"
    echo
}

# Execute main function with all arguments
main "$@"
