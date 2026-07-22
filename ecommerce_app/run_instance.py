import argparse

from app import create_app


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Start a named ecommerce application instance."
        )
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Instance name displayed in pages and headers.",
    )

    parser.add_argument(
        "--port",
        required=True,
        type=int,
        help="TCP port used by this Flask instance.",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface. Default: 0.0.0.0",
    )

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    app = create_app(
        {
            "INSTANCE_NAME": args.name,
        }
    )

    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
