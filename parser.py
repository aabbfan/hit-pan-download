import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description='HITPanDownload - download tool with cookie authentication'
    )
    parser.add_argument('--cookie', type=str,
                        help='Cookie string for authentication')
    parser.add_argument('--window-size', nargs=2, type=int,
                        metavar=('WIDTH', 'HEIGHT'), default=[800, 600],
                        help='Webview window size (default: 800 600)')
    return parser.parse_args()
