"""Entry point del sistema di pronostici calcistici."""

import argparse

import config
from ui.cli import run_cli, run_analysis, DEFAULT_DATA_PATH


def _parse_args() -> argparse.Namespace:
    """Configura e analizza gli argomenti da riga di comando."""
    parser = argparse.ArgumentParser(
        description="Sistema di pronostici calcistici Asian Handicap & Total",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        default=None,
        help=f"Percorso al file JSON delle partite (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--edge",
        metavar="FLOAT",
        type=float,
        default=None,
        help=f"Edge minimo per filtrare i pronostici (default: {config.MIN_EDGE_THRESHOLD})",
    )
    parser.add_argument(
        "--only-sharp",
        action="store_true",
        help="Mostra solo i pronostici con segnale sharp",
    )
    parser.add_argument(
        "--only-ah",
        action="store_true",
        help="Mostra solo i pronostici del mercato Asian Handicap",
    )
    parser.add_argument(
        "--only-total",
        action="store_true",
        help="Mostra solo i pronostici del mercato Asian Total",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Esegue l'analisi e termina senza aprire il menu interattivo",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Se almeno un argomento non-interattivo è presente, esegui direttamente l'analisi
    if args.no_interactive or args.file or args.edge is not None or args.only_sharp or args.only_ah or args.only_total:
        filepath = args.file if args.file else DEFAULT_DATA_PATH
        min_edge = args.edge if args.edge is not None else config.MIN_EDGE_THRESHOLD
        run_analysis(
            filepath=filepath,
            min_edge=min_edge,
            only_sharp=args.only_sharp,
            only_ah=args.only_ah,
            only_total=args.only_total,
        )
    else:
        # Comportamento predefinito: CLI interattiva
        run_cli()
