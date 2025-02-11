from __future__ import print_function
import warnings
import torch.utils.data as data
from PIL import Image
import os
import os.path
import errno
import gzip
import numpy as np
import torch
import codecs
from torchvision.datasets.utils import download_url

def makedir_exist_ok(dirpath):
    """
    Python2 support for os.makedirs(.., exist_ok=True)
    """
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

class SNIST(data.Dataset):
    """`SNIST <https://github.com/LukasMosser/SNIST>`_ Dataset.

    Args:
        root (string): Root directory of dataset where ``SNIST/processed/training.pt``
            and  ``SNIST/processed/test.pt`` exist.
        train (bool, optional): If True, creates dataset from ``training.pt``,
            otherwise from ``test.pt``.
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.
        transform (callable, optional): A function/transform that  takes in an PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
    """
    urls = [
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/train/train_amplitudes.npy',
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/train/train_velocities.npy',
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/test/test_amplitudes.npy',
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/test/test_velocities.npy',
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/test/test_amplitudes_noise_1.npy',
        'https://raw.githubusercontent.com/LukasMosser/SNIST/master/data/test/test_amplitudes_noise_2.npy'
    ]
    training_file = 'training.pt'
    test_file_noise_0 = 'test_noise_0.pt'
    test_file_noise_1 = 'test_noise_1.pt'
    test_file_noise_2 = 'test_noise_2.pt'

    @property
    def train_labels(self):
        warnings.warn("train_labels has been renamed targets")
        return self.targets

    @property
    def test_labels(self):
        warnings.warn("test_labels has been renamed targets")
        return self.targets

    @property
    def train_data(self):
        warnings.warn("train_data has been renamed data")
        return self.data

    @property
    def test_data(self):
        warnings.warn("test_data has been renamed data")
        return self.data

    def __init__(self, root, train=True, noise=0, transform=None, target_transform=None, download=False):
        self.root = os.path.expanduser(root)
        self.transform = transform
        self.target_transform = target_transform
        self.train = train  # training set or test set

        if download:
            self.download()

        if not self._check_exists():
            raise RuntimeError('Dataset not found.' +
                               ' You can use download=True to download it')

        if self.train:
            data_file = self.training_file
        else:
            if noise == 0:
                data_file = self.test_file_noise_0
            elif noise == 1:
                data_file = self.test_file_noise_1
            elif noise == 2:
                data_file = self.test_file_noise_2

        self.data, self.targets = torch.load(os.path.join(self.processed_folder, data_file))

    def __getitem__(self, index):
        """
        Args:
            index (int): Index

        Returns:
            tuple: (image, target) where target is index of the target class.
        """
        img, target = self.data[index], self.targets[index]

        # doing this so that it is consistent with all other datasets
        # to return a PIL Image
        #img = Image.fromarray(img.numpy(), mode='L')

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        return len(self.data)

    @property
    def raw_folder(self):
        return os.path.join(self.root, self.__class__.__name__, 'raw')

    @property
    def processed_folder(self):
        return os.path.join(self.root, self.__class__.__name__, 'processed')

    def _check_exists(self):
        return os.path.exists(os.path.join(self.processed_folder, self.training_file)) and \
            os.path.exists(os.path.join(self.processed_folder, self.test_file_noise_0)) and \
            os.path.exists(os.path.join(self.processed_folder, self.test_file_noise_1)) and \
            os.path.exists(os.path.join(self.processed_folder, self.test_file_noise_2))

    def download(self):
        """Download the SNIST data if it doesn't exist in processed_folder already."""

        if self._check_exists():
            return

        makedir_exist_ok(self.raw_folder)
        makedir_exist_ok(self.processed_folder)

        # download files
        for url in self.urls:
            filename = url.rpartition('/')[2]
            file_path = os.path.join(self.raw_folder, filename)
            download_url(url, root=self.raw_folder, filename=filename, md5=None)

        # process and save as torch files
        print('Processing...')

        training_set = (
            read_amplitude_file(os.path.join(self.raw_folder, 'train_amplitudes.npy')),
            read_velocity_file(os.path.join(self.raw_folder, 'train_velocities.npy'))
        )
        test_set_noise_0 = (
            read_amplitude_file(os.path.join(self.raw_folder, 'test_amplitudes.npy')),
            read_velocity_file(os.path.join(self.raw_folder, 'test_velocities.npy'))
        )

        test_set_noise_1 = (
            read_amplitude_file(os.path.join(self.raw_folder, 'test_amplitudes_noise_1.npy')),
            read_velocity_file(os.path.join(self.raw_folder, 'test_velocities.npy'))
        )

        test_set_noise_2 = (
            read_amplitude_file(os.path.join(self.raw_folder, 'test_amplitudes_noise_2.npy')),
            read_velocity_file(os.path.join(self.raw_folder, 'test_velocities.npy'))
        )

        with open(os.path.join(self.processed_folder, self.training_file), 'wb') as f:
            torch.save(training_set, f)
        with open(os.path.join(self.processed_folder, self.test_file_noise_0), 'wb') as f:
            torch.save(test_set_noise_0, f)
        with open(os.path.join(self.processed_folder, self.test_file_noise_1), 'wb') as f:
            torch.save(test_set_noise_1, f)
        with open(os.path.join(self.processed_folder, self.test_file_noise_2), 'wb') as f:
            torch.save(test_set_noise_2, f)

        print('Done!')

    def __repr__(self):
        fmt_str = 'Dataset ' + self.__class__.__name__ + '\n'
        fmt_str += '    Number of datapoints: {}\n'.format(self.__len__())
        tmp = 'train' if self.train is True else 'test'
        fmt_str += '    Split: {}\n'.format(tmp)
        fmt_str += '    Root Location: {}\n'.format(self.root)
        tmp = '    Transforms (if any): '
        fmt_str += '{0}{1}\n'.format(tmp, self.transform.__repr__().replace('\n', '\n' + ' ' * len(tmp)))
        tmp = '    Target Transforms (if any): '
        fmt_str += '{0}{1}'.format(tmp, self.target_transform.__repr__().replace('\n', '\n' + ' ' * len(tmp)))
        return fmt_str


def get_int(b):
    return int(codecs.encode(b, 'hex'), 16)

def read_velocity_file(path):
    data = np.load(path)
    return torch.from_numpy(data).float()


def read_amplitude_file(path):
    data = np.load(path)
    return torch.from_numpy(data).view(data.shape[0], 1, data.shape[1], data.shape[2]).float()
