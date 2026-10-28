"""Remux rendered clips with the original audio/captions and verify preservation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess


def packets(path):
    response = subprocess.run([
        'ffprobe', '-v', 'error', '-show_packets', '-show_data_hash', 'sha256',
        '-show_entries', 'packet=stream_index,pts_time,data_hash', '-of', 'json',
        str(path)], capture_output=True, text=True, check=True)
    return json.loads(response.stdout)['packets']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--original', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--changed-from', type=float, required=True,
                    help='Seconds at which the replaced tail begins, from timings.json')
    args = ap.parse_args()
    if args.original.resolve() == args.output.resolve():
        ap.error('Use a separate output file; preserve the original')
    if args.changed_from < 0:
        ap.error('--changed-from must be nonnegative')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Assumes this example's stream order: video, audio, optional captions.
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat',
        '-safe', '0', '-i', str(args.build / 'clips.txt'), '-i', str(args.original),
        '-map', '0:v:0', '-map', '1:a:0', '-map', '1:s:0?', '-map_metadata', '1',
        '-c', 'copy', '-movflags', '+faststart', str(args.output)], check=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        old, new = list(pool.map(packets, [args.original, args.output]))
    for stream, label in [(1, 'Audio'), (2, 'Captions')]:
        def selected(items):
            return [(x.get('pts_time'), x['data_hash']) for x in items
                    if x['stream_index'] == stream]
        if selected(old) != selected(new):
            raise SystemExit(f'{label} changed: inspect the output before delivery')
        print(f'{label}: original packet data and timestamps preserved')
    def prefix(items):
        return [(x.get('pts_time'), x['data_hash']) for x in items
                if x['stream_index'] == 0
                and float(x['pts_time']) < args.changed_from - 0.0001]
    if prefix(old) != prefix(new):
        raise SystemExit('Video before the requested change differs')
    print(f'{len(prefix(old))} preceding video packets preserved exactly')
    def duration(path):
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'json', str(path)], capture_output=True, text=True, check=True)
        return float(json.loads(r.stdout)['format']['duration'])
    if abs(duration(args.original) - duration(args.output)) > 0.05:
        raise SystemExit('Duration changed; a card-only edit should preserve the timeline')
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
