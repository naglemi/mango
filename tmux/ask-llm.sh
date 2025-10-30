#!/usr/bin/env bash
# Ask LLM - Main orchestration script that ties together file selection, model selection, and interactive chat
# Integrates with Claude's MCP system for actual LLM queries

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo " Ask LLM - Interactive AI Assistant"
echo "======================================"
echo

# Step 1: File Selection
echo " Step 1: Select files to include (optional)"
echo "Press Enter to skip file selection, or any other key to select files..."
read -n 1 -s SKIP_FILES

SELECTED_FILES=""
FILES_CONTENT=()

if [[ "$SKIP_FILES" != "" ]]; then
    echo
    echo " Select files to include as context..."

    # Create temporary file for communication
    TEMP_SELECTION="/tmp/ask-llm-selection-$$"

    # Run the file selector
    python3 "$SCRIPT_DIR/ask-llm-file-selector.py" > "$TEMP_SELECTION"

    # Read the selection
    if [[ -f "$TEMP_SELECTION" ]]; then
        OUTPUT_LINE="$(head -n 1 "$TEMP_SELECTION")"
        if [[ "$OUTPUT_LINE" == SELECTED_FILES=* ]]; then
            SELECTED_FILES="${OUTPUT_LINE#SELECTED_FILES=}"
        fi
        rm -f "$TEMP_SELECTION"
    fi

    # Process selected files if any
    if [[ -n "$SELECTED_FILES" && "$SELECTED_FILES" != '""' ]]; then
        echo " Processing selected files..."
        eval "FILES_ARRAY=($SELECTED_FILES)"

        # Read file contents
        for file in "${FILES_ARRAY[@]}"; do
            # Remove quotes from file path
            file="${file//\"/}"

            if [[ -f "$file" ]]; then
                echo "   Reading: $file"
            else
                echo "   Not found: $file"
            fi
        done
    else
        echo "No files selected."
    fi
else
    echo
    echo "Skipping file selection."
fi

echo

# Step 2: Model Selection
echo " Step 2: Select AI models to query"

# Create temporary file for model selection
TEMP_MODELS="/tmp/ask-llm-models-$$"

# Run the model selector
python3 "$SCRIPT_DIR/ask-llm-model-selector.py" > "$TEMP_MODELS"

# Parse model selection
SELECTED_MODELS=""
MCP_TOOLS=""
COMPARISON_MODE="false"

if [[ -f "$TEMP_MODELS" ]]; then
    while IFS= read -r line; do
        if [[ "$line" == SELECTED_MODELS=* ]]; then
            SELECTED_MODELS="${line#SELECTED_MODELS=}"
        elif [[ "$line" == MCP_TOOLS=* ]]; then
            MCP_TOOLS="${line#MCP_TOOLS=}"
        elif [[ "$line" == COMPARISON_MODE=* ]]; then
            COMPARISON_MODE="${line#COMPARISON_MODE=}"
        fi
    done < "$TEMP_MODELS"
    rm -f "$TEMP_MODELS"
fi

# Check if models were selected
if [[ -z "$SELECTED_MODELS" || "$SELECTED_MODELS" == "" ]]; then
    echo " No models selected. Exiting."
    exit 1
fi

echo " Selected models: $SELECTED_MODELS"
if [[ "$COMPARISON_MODE" == "true" ]]; then
    echo " Mode: Comparison (side-by-side responses)"
else
    echo " Mode: Sequential (one after another)"
fi
echo

# Step 3: Context Selection (optional)
echo " Step 3: Include previous responses as context (optional)"
echo "Press Enter to skip context, or any other key to select previous responses..."
read -n 1 -s SKIP_CONTEXT

CONTEXT_STRINGS=()

if [[ "$SKIP_CONTEXT" != "" ]]; then
    echo
    echo " Select previous responses to include as context..."

    # Create temporary file for context selection
    TEMP_CONTEXT="/tmp/ask-llm-context-$$"

    # Run the context selector
    python3 "$SCRIPT_DIR/ask-llm-context-selector.py" > "$TEMP_CONTEXT"

    # Parse context selection
    if [[ -f "$TEMP_CONTEXT" ]]; then
        CONTEXT_COUNT=0
        while IFS= read -r line; do
            if [[ "$line" == CONTEXT_COUNT=* ]]; then
                CONTEXT_COUNT="${line#CONTEXT_COUNT=}"
            fi
        done < "$TEMP_CONTEXT"
        rm -f "$TEMP_CONTEXT"

        if [[ "$CONTEXT_COUNT" -gt 0 ]]; then
            echo " Selected $CONTEXT_COUNT previous responses as context"
        else
            echo "No previous context selected."
        fi
    fi
else
    echo
    echo "Skipping context selection."
fi

echo

# Step 4: Get the question
echo " Step 4: Enter your question"
echo "=============================="
echo -n "Question: "
read -r QUESTION

if [[ -z "$QUESTION" ]]; then
    echo " No question entered. Exiting."
    exit 1
fi

echo
echo " Starting interactive chat session..."
echo "======================================"
echo "Question: $QUESTION"
echo "Models: $SELECTED_MODELS"
echo "Mode: $(if [[ "$COMPARISON_MODE" == "true" ]]; then echo "Comparison"; else echo "Sequential"; fi)"
echo

# Step 5: Start the interactive chat
# For now, we'll show what would happen and provide a placeholder implementation
echo " This would now start the interactive chat with the selected models..."
echo

# Parse the models and tools arrays
eval "MODELS_ARRAY=($SELECTED_MODELS)"
eval "TOOLS_ARRAY=($MCP_TOOLS)"

echo "Selected models and their MCP tools:"
for i in "${!MODELS_ARRAY[@]}"; do
    echo "  ${MODELS_ARRAY[i]} -> ${TOOLS_ARRAY[i]}"
done

echo
echo " Question to ask:"
echo "$QUESTION"
echo

# If files were selected, show them
if [[ -n "$SELECTED_FILES" && "$SELECTED_FILES" != '""' ]]; then
    echo " Files to include:"
    eval "FILES_ARRAY=($SELECTED_FILES)"
    for file in "${FILES_ARRAY[@]}"; do
        file="${file//\"/}"
        if [[ -f "$file" ]]; then
            echo "   $file"
        fi
    done
    echo
fi

echo " PLACEHOLDER: Interactive chat would start here"
echo "Features that would be available:"
echo "  • Real-time responses from selected models"
echo "  • Q to quit, A to ask follow-up questions"
echo "  • Automatic saving to ask_llm_outputs/ directory"
echo "  • Context from previous conversations"
echo "  • File contents included in prompts"

if [[ "$COMPARISON_MODE" == "true" ]]; then
    echo "  • Side-by-side comparison of all model responses"
else
    echo "  • Sequential responses from each model"
fi

echo
echo " To implement the actual LLM integration, this script would:"
echo "   1. Create a Claude session with the selected MCP tools"
echo "   2. Format the question with file contents and context"
echo "   3. Call each MCP tool (${MCP_TOOLS})"
echo "   4. Display responses and handle user interactions"
echo "   5. Save everything to organized output files"

echo
echo "Press any key to exit this demo..."
read -n 1

# Cleanup
rm -f /tmp/ask-llm-*-$$

echo
echo " Ask LLM demo completed!"