import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


def inspect_csv(file_path):
    path = Path(file_path).expanduser()

    if not path.is_file():
        console.print("[red]File not found.[/red]")
        return

    try:
        df = pd.read_csv(path)
    except Exception as error:
        console.print(f"[red]Could not read CSV: {error}[/red]")
        return

    table = Table(title=f"CSV Overview: {path.name}")

    table.add_column("Column", style="cyan")
    table.add_column("Data Type", style="magenta")
    table.add_column("Missing Values", justify="right")
    table.add_column("Unique Values", justify="right")

    for column in df.columns:
        table.add_row(
            str(column),
            str(df[column].dtype),
            str(df[column].isna().sum()),
            str(df[column].nunique()),
        )

    console.print(table)
    console.print(f"\n[bold]Rows:[/bold] {len(df):,}")
    console.print(f"[bold]Columns:[/bold] {len(df.columns):,}")
    console.print(f"[bold]File size:[/bold] {path.stat().st_size:,} bytes")

def detect_issues(file_path):
    path = Path(file_path).expanduser()

    if not path.is_file():
        console.print("[red]File not found.[/red]")
        return

    try:
        df = pd.read_csv(path)
    except Exception as error:
        console.print(f"[red]Could not read CSV: {error}[/red]")
        return

    from rich.table import Table

    table = Table(title=f"Data Quality Report: {path.name}")
    table.add_column("Issue", style="cyan")
    table.add_column("Column / Location")
    table.add_column("Count", justify="right", style="yellow")
    table.add_column("Details")

    issues_found = 0

    # 1. Missing values
    for column in df.columns:
        missing = int(df[column].isna().sum())

        if missing:
            table.add_row(
                "Missing values",
                str(column),
                str(missing),
                "Rows contain empty values",
            )
            issues_found += missing

    # 2. Inconsistent formatting
    for column in df.select_dtypes(include=["object", "string"]).columns:
        values = df[column].dropna().astype(str)
        normalized = values.str.strip().str.casefold()
        inconsistent = int((values != normalized).sum())

        if inconsistent:
            table.add_row(
                "Inconsistent formatting",
                str(column),
                str(inconsistent),
                "Whitespace or capitalization differs",
            )
            issues_found += inconsistent

    # 3. Exact duplicate rows
    duplicate_count = int(df.duplicated().sum())

    if duplicate_count:
        table.add_row(
            "Duplicate rows",
            "Entire row",
            str(duplicate_count),
            "Rows exactly match earlier rows",
        )
        issues_found += duplicate_count

    # 4. Suspicious numeric values
    for column in df.select_dtypes(include=["number"]).columns:
        negative_count = int((df[column] < 0).sum())

        if negative_count:
            table.add_row(
                "Negative values",
                str(column),
                str(negative_count),
                "Review whether negative values are valid",
            )
            issues_found += negative_count

    console.print(table)

    if issues_found:
        console.print(
            f"\n[yellow]Found {issues_found} potential data quality issues.[/yellow]"
        )
    else:
        console.print("\n[green]No issues detected by these checks.[/green]")

    console.print(
        "[dim]Findings are candidates for review; they are not automatically corrected.[/dim]"
    )

def create_quality_summary(file_path):
    path = Path(file_path).expanduser()

    if not path.is_file():
        console.print("[red]File not found.[/red]")
        return None

    try:
        df = pd.read_csv(path)
    except Exception as error:
        console.print(f"[red]Could not read CSV: {error}[/red]")
        return None

    summary = {
        "file_name": path.name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "missing_values": {
            str(column): int(count)
            for column, count in df.isna().sum().items()
            if count > 0
        },
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "formatting_issues": {},
        "negative_numeric_values": {},
    }

    for column in df.select_dtypes(
        include=["object", "string"]
    ).columns:
        values = df[column].dropna().astype(str)
        normalized = values.str.strip().str.casefold()
        count = int((values != normalized).sum())

        if count:
            summary["formatting_issues"][str(column)] = count

    for column in df.select_dtypes(include=["number"]).columns:
        count = int((df[column] < 0).sum())

        if count:
            summary["negative_numeric_values"][str(column)] = count

    return summary


def preview_changes(file_path):
    from pathlib import Path

    import pandas as pd
    from rich.console import Console
    from rich.table import Table

    console = Console()
    path = Path(file_path)

    try:
        df = pd.read_csv(path)
    except Exception as error:
        console.print(f"[red]Could not read CSV: {error}[/red]")
        return

    categories = {
        "Whitespace cleanup": [],
        "Approved business rules": [],
    }

    # Find leading or trailing whitespace.
    for column in df.select_dtypes(include=["object"]).columns:
        for index, value in df[column].items():
            if isinstance(value, str) and value != value.strip():
                categories["Whitespace cleanup"].append({
                    "row": index + 2,
                    "column": column,
                    "original": value,
                    "proposed": value.strip(),
                    "reason": "Remove leading/trailing whitespace",
                })

    # Preview the explicitly approved Bangalore -> Bengaluru rule.
    if "city" in df.columns:
        for index, value in df["city"].items():
            if isinstance(value, str) and value.strip() == "Bangalore":
                categories["Approved business rules"].append({
                    "row": index + 2,
                    "column": "city",
                    "original": value,
                    "proposed": "Bengaluru",
                    "reason": "Bangalore -> Bengaluru",
                })

    total_changes = sum(len(changes) for changes in categories.values())

    if total_changes == 0:
        console.print("[green]No supported changes to preview.[/green]")
        return categories

    for category, changes in categories.items():
        if not changes:
            continue

        table = Table(
            title=f"{category} ({len(changes)} change(s))"
        )
        table.add_column("CSV Row", style="cyan")
        table.add_column("Column")
        table.add_column("Original Value")
        table.add_column("Proposed Value", style="green")
        table.add_column("Reason")

        for change in changes:
            table.add_row(
                str(change["row"]),
                change["column"],
                str(change["original"]),
                str(change["proposed"]),
                change["reason"],
            )

        console.print(table)

    console.print(
        f"\nFound [bold]{total_changes}[/bold] proposed change(s) "
        f"across {sum(bool(changes) for changes in categories.values())} "
        "category/categories."
    )
    console.print(
        "[yellow]Preview only: the original CSV has not been modified.[/yellow]"
    )

    return categories

def apply_approved_changes(file_path, approved_categories):
    from pathlib import Path

    import pandas as pd
    from rich.console import Console

    console = Console()
    path = Path(file_path)

    try:
        df = pd.read_csv(path)
    except Exception as error:
        console.print(f"[red]Could not read CSV: {error}[/red]")
        return None

    changes_applied = 0

    # Apply whitespace cleanup only if its category was approved.
    if "Whitespace cleanup" in approved_categories:
        for column in df.select_dtypes(include=["object"]).columns:
            original = df[column].copy()
            df[column] = df[column].apply(
                lambda value: value.strip()
                if isinstance(value, str)
                else value
            )
            changes_applied += int((original != df[column]).sum())

    # Apply the saved Bangalore -> Bengaluru business rule
    # only if its category was approved.
    if "Approved business rules" in approved_categories:
        if "city" in df.columns:
            original = df["city"].copy()
            df["city"] = df["city"].apply(
                lambda value: "Bengaluru"
                if isinstance(value, str)
                and value.strip() == "Bangalore"
                else value
            )
            changes_applied += int((original != df["city"]).sum())

    output_path = path.with_name(f"{path.stem}_cleaned{path.suffix}")

    if output_path.exists():
        from rich.prompt import Prompt

        while True:
            filename = Prompt.ask(f"[yellow]{output_path.name} already exists. " "Enter a different output filename[/yellow]").strip()

            if not filename:
                console.print("[red]Filename cannot be empty.[/red]")
                continue

            candidate = Path(filename)

            if not candidate.is_absolute():
                candidate = path.parent / candidate

            if candidate.resolve() == path.resolve():
                console.print("[red]Cannot overwrite the original CSV.[/red]")
                continue

            if candidate.exists():
                console.print("[red]That file already exists. Choose another name.[/red]")
                continue

            output_path = candidate
            break

    try:
        df.to_csv(output_path, index=False)
    except Exception as error:
        console.print(f"[red]Could not save cleaned CSV: {error}[/red]")
        return None

    console.print(f"[green]Saved cleaned CSV to: {output_path}[/green]")
    console.print(f"Changes applied: {changes_applied}")

    try:
        save_cleaning_history(
            original_file=path,
            output_file=output_path,
            approved_categories=approved_categories,
            changes_applied=changes_applied,
        )
        console.print("[dim]Cleaning operation recorded in history.[/dim]")
    except Exception as error:
        console.print(
            f"[yellow]CSV saved, but history could not be recorded: "
            f"{error}[/yellow]"
        )

    return output_path

def initialize_history_db():
    db_path = Path(__file__).resolve().parent / "fixmycsv.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cleaning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_file TEXT NOT NULL,
                output_file TEXT NOT NULL,
                approved_categories TEXT NOT NULL,
                changes_applied INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
initialize_history_db()

def save_cleaning_history(
    original_file,
    output_file,
    approved_categories,
    changes_applied,
):
    db_path = Path(__file__).resolve().parent / "fixmycsv.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            INSERT INTO cleaning_history (
                original_file,
                output_file,
                approved_categories,
                changes_applied,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(original_file),
            str(output_file),
            ", ".join(approved_categories),
            changes_applied,
            datetime.now().astimezone().isoformat(timespec="seconds"),
        ))

def get_cleaning_history(limit=20):
    db_path = Path(__file__).resolve().parent / "fixmycsv.db"

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT
                id,
                original_file,
                output_file,
                approved_categories,
                changes_applied,
                timestamp
            FROM cleaning_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]