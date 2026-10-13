import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from core import (
    inspect_csv,
    detect_issues,
    create_quality_summary,
    preview_changes,
    apply_approved_changes,
    get_cleaning_history,
)
from engine import (
    get_cleaning_suggestions,
    save_cleaning_rule,
    search_cleaning_rules,
)

console = Console()
RULE_QUERY = "Approved cleaning rules for retail CSV data"


def show_banner():
    title = Text("FixMyCSV", style="bold cyan")
    subtitle = Text("Retail Data Cleaning Assistant", style="bold white")

    banner = Text.assemble(title, "\n", subtitle)

    console.print(
        Panel(
            Align.center(banner),
            border_style="cyan",
            padding=(1, 2),
            expand=True
        )
    )

    console.print(
        Align.center("Turn messy retail spreadsheets into trustworthy data.\n")
    )


def show_menu():
    return questionary.select(
        "What would you like to do?",
        choices=[
            "Inspect a CSV file",
            "Find data quality issues",
            "Get AI cleaning suggestions",
            "Preview and clean a CSV",
            "View cleaning history",
            "Save an approved cleaning rule",
            "Exit",
        ],
        instruction="(Use arrow keys and Enter)",
    ).ask()


def choose_csv():
    return questionary.path("Enter the CSV file path:").ask()


def retrieve_rule_text():
    memories = search_cleaning_rules(RULE_QUERY)
    rules = []
    for memory in memories:
        if isinstance(memory, dict):
            content = memory.get("content", "")
        else:
            content = str(memory)
        if content:
            rules.append(content)
    return rules


def preview_and_clean(file_path):
    categories = preview_changes(file_path)
    if not categories:
        return

    approved_categories = []
    for category, changes in categories.items():
        if not changes:
            continue

        approved = questionary.confirm(
            f"Approve all {len(changes)} change(s) in '{category}'?",
            default=False,
        ).ask()

        if approved:
            approved_categories.append(category)

    if not approved_categories:
        console.print("[yellow]No categories approved. No output file was created.[/yellow]")
        return

    confirm_save = questionary.confirm(
        "Apply approved changes and save a cleaned copy?",
        default=False,
    ).ask()

    if confirm_save:
        apply_approved_changes(file_path, approved_categories)
    else:
        console.print("[yellow]Saving cancelled. No output file was created.[/yellow]")


def show_history():
    history = get_cleaning_history()
    if not history:
        console.print("[yellow]No cleaning history found yet.[/yellow]")
        return

    table = Table(title="Cleaning History")
    table.add_column("ID", style="cyan")
    table.add_column("Original File")
    table.add_column("Output File")
    table.add_column("Approved Categories")
    table.add_column("Changes Applied", justify="right")
    table.add_column("Timestamp")

    for record in history:
        table.add_row(
            str(record["id"]),
            record["original_file"],
            record["output_file"],
            record["approved_categories"],
            str(record["changes_applied"]),
            record["timestamp"],
        )
    console.print(table)


def main():
    while True:
        console.clear()
        show_banner()
        choice = show_menu()

        if choice is None or choice == "Exit":
            console.print("\nGoodbye!", style="bold cyan")
            break

        try:
            if choice == "Inspect a CSV file":
                file_path = choose_csv()
                if file_path:
                    inspect_csv(file_path)

            elif choice == "Find data quality issues":
                file_path = choose_csv()
                if file_path:
                    detect_issues(file_path)

            elif choice == "Get AI cleaning suggestions":
                file_path = choose_csv()
                if file_path:
                    report = create_quality_summary(file_path)
                    if report is not None:
                        try:
                            rules = retrieve_rule_text()
                        except Exception as error:
                            rules = []
                            console.print(
                                f"[yellow]Could not retrieve saved rules: {error}[/yellow]"
                            )

                        with console.status("[cyan]Asking Gemma for suggestions...[/cyan]"):
                            suggestions = get_cleaning_suggestions(report, rules)

                        console.print(
                            Panel(
                                suggestions,
                                title="AI Cleaning Suggestions",
                                border_style="cyan",
                            )
                        )

            elif choice == "Preview and clean a CSV":
                file_path = choose_csv()
                if file_path:
                    preview_and_clean(file_path)

            elif choice == "View cleaning history":
                show_history()

            elif choice == "Save an approved cleaning rule":
                rule = questionary.text(
                    "Describe the business rule to remember:"
                ).ask()

                if rule and rule.strip():
                    approved = questionary.confirm(
                        f"Save this rule?\n\n{rule}",
                        default=False,
                    ).ask()

                    if approved:
                        save_cleaning_rule(
                            f"Business-approved cleaning rule: {rule.strip()}"
                        )
                        console.print("[green]Rule saved successfully.[/green]")

        except Exception as error:
            console.print(f"[red]Could not complete the request: {error}[/red]")

        console.input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()
