def confirm_production() -> None:
    """Require explicit double confirmation before touching the production database."""
    print("WARNING: You are about to modify the PRODUCTION database.")
    if input("Type 'production' to continue: ").strip() != "production":
        raise SystemExit("Aborted.")
    if input("Type 'yes' to confirm: ").strip().lower() != "yes":
        raise SystemExit("Aborted.")
