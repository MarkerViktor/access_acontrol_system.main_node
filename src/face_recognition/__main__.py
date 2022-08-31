from pathlib import Path
from argparse import ArgumentParser

import numpy as np
from PIL import Image, UnidentifiedImageError

from .two_step import FaceImageNormalizer
from .backends.dlib_ import DlibDetector, DlibNormalizer, DlibRecognizer


def make_parser():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input',
                        dest='input', type=Path,
                        required=True, default=None)
    parser.add_argument('-m', '--mode',
                        dest='mode', type=str,
                        choices=['calc', 'norm'],
                        help='What you want to do:'
                             '\tMake descriptor(s) and print'
                             '\tNormalize image(s) and save (each) as "norm_..."',
                        required=True)
    return parser


image_normalizer = FaceImageNormalizer(
    detector=DlibDetector(),
    normalizer=DlibNormalizer()
)
recognizer = DlibRecognizer()
image_file_types = ['*.jpg', '*.png', '*.JPEG', '*.JPG']


def main():
    args = make_parser().parse_args()

    input = args.input
    mode = args.mode

    files: list[Path]
    if input.is_file():
        files = [input]
    elif input.is_dir():
        files = [file for img_type in image_file_types for file in input.glob(img_type)]
    else:
        print('Wrong input!')
        return

    for file in files:
        print('Performing:', file)

        try:
            input_image = Image.open(file)
        except UnidentifiedImageError:
            print('\tBad image format – skipped')
        normalized_image = image_normalizer.normalize(np.array(input_image))
        if normalized_image is None:
            print("\tCan't normalize image – skipped")
            continue

        match mode:
            case 'calc':
                descriptor = list(recognizer.extract_features(normalized_image))
                print('\tOutput:')
                print('{' + ',\n'.join(str(feature) for feature in descriptor) + '}\n')
            case 'norm':
                output_image_path = file.parent / ('normalized_' + file.name)
                print('\tOutput file:', output_image_path)
                Image.fromarray(normalized_image).save(output_image_path)


if __name__ == '__main__':
    main()
