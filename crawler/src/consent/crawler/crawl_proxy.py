from typing import Dict, List, Optional

class CrawlProxy:
    location_to_ips: Dict[str, List[Optional[str]]] = {
        'capetown': ['13.246.21.145', '13.246.50.151'],
        'ireland': ['52.209.118.202', '3.253.48.140'],
        'london': ['18.130.180.0', '18.175.239.213'],
        'mi': [None],
        'sf': ['54.177.16.240', '54.193.10.55'],
        'toronto': ['3.97.12.2', '35.183.235.58'],
        'singapore': ['54.179.68.81', '13.214.212.71'],
        'sydney': ['54.66.247.95', '13.55.59.247'],
        # 'aus': ['3.27.64.178', '54.206.89.211'],
        # 'ca': ['54.193.72.194', '54.241.103.228'],
        # 'can': ['3.99.224.204', '35.182.213.230'],
        # 'ie': ['54.78.209.135', '34.252.247.174'],
        # 'sg': ['13.215.49.17', '54.251.92.92'],
        # 'uk': ['3.8.205.52', '18.133.134.237'],
        # 'za': ['18.228.18.101', '15.228.149.216'],
    }
    location_to_idx = { location: 0 for location in location_to_ips}

    @classmethod
    def get_next_ip(cls, location: str) -> Optional[str]:
        ips = cls.location_to_ips[location]
        next_idx = (cls.location_to_idx[location]+ 1) % len(ips)
        cls.location_to_idx[location] = next_idx
        ip = cls.location_to_ips[location][next_idx]
        return f"socks5://{ip}:8888" if ip is not None else None

    @classmethod
    def get_proxy_url_ip(cls, location, verbose=0) -> Optional[str]:
        assert set(cls.location_to_ips.keys()) == set(cls.location_to_idx.keys()), \
            f"{cls.location_to_ips=} must have same keys with {cls.location_to_idx=}"

        assert location in cls.location_to_ips, f'Invalid location {location}, should be one of {list(cls.location_to_ips.keys())}'
        proxy_url = cls.get_next_ip(location)

        if verbose >= 2:
            print(f'{location=} {proxy_url=}')
        return proxy_url

def test():
    assert CrawlProxy.get_proxy_url_ip('de') != CrawlProxy.get_proxy_url_ip('de'), "The proxy ips should be rotated"
    ips = [CrawlProxy.get_proxy_url_ip('de') for _ in range(10)]
    assert len(set(ips)) == len(CrawlProxy.de_proxy_ips)

if __name__ == '__main__':
    test()
    print("Test passed.")