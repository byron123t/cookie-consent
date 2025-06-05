
class CrawlProxy:
    location_to_ips = {
        'ca': ['164.90.146.84', '147.182.254.242'],
        'de': ['138.68.86.77', '134.122.84.134'],
        'uk': ['159.65.52.217', '68.183.46.217']
    }
    location_to_idx = {
        'ca': 0,
        'de': 0,
        'uk': 0
    }

    @classmethod
    def get_next_ip(cls, location: str) -> str:
        ips = cls.location_to_ips[location]
        next_idx = (cls.location_to_idx[location]+ 1) % len(ips)
        cls.location_to_idx[location] = next_idx
        ip = cls.location_to_ips[location][next_idx]
        return f"socks5://{ip}:8888"

    @classmethod
    def get_proxy_url_ip(cls, location, verbose=0):
        assert set(cls.location_to_ips.keys()) == set(cls.location_to_idx.keys()), \
            f"{cls.location_to_ips=} must have same keys with {cls.location_to_idx=}"

        if location in cls.location_to_ips:
            proxy_url = cls.get_next_ip(location)
        else:
            raise Exception(f"invalid location {location}, should be 'ca', or 'de'")

        if verbose >= 2:
            print(f'{location=} {proxy_url=}')
        return proxy_url
