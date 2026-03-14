"""
Tuya OEM API - Get local keys via Tuya/Smart Life app credentials (no IoT Cloud needed).
Based on https://github.com/blakadder/tuya-uncover
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional

import requests

_API_VERSION = "1.0"
_USER_AGENT = "TY-UA=APP/Android/1.1.6/SDK/null"

# OEM vendor client_id and secret for Tuya mobile apps
VENDORS: Dict[str, Dict[str, str]] = {
    "smartlife": {"brand": "Smart Life", "client_id": "ekmnwp9f5pnh3trdtpgy",
                  "secret": "0F:C3:61:99:9C:C0:C3:5B:A8:AC:A5:7D:AA:55:93:A2:0C:F5:57:27:70:2E:A8:5A:D7:B3:22:89:49:F8:88:FE_jfg5rs5kkmrj5mxahugvucrsvw43t48x_r3me7ghmxjevrvnpemwmhw3fxtacphyg"},
    "tuya": {"brand": "Tuya", "client_id": "3fjrekuxank9eaej3gcx",
             "secret": "93:21:9F:C2:73:E2:20:0F:4A:DE:E5:F7:19:1D:C6:56:BA:2A:2D:7B:2F:F5:D2:4C:D5:5C:4B:61:55:00:1E:40_aq7xvqcyqcnegvew793pqjmhv77rneqc_vay9g59g9g99qf3rtqptmc3emhkanwkx"},
    "gosund": {"brand": "Gosund", "client_id": "pwhnn4fa7ydkakf3nehn",
               "secret": "A_pqdyxyx3uhk337sxxumdgfry3awaxysm_wm8hvxahqhcvvnpqgurympm4ppfgxxnm"},
    "ledvance": {"brand": "Ledvance", "client_id": "fx3fvkvusmw45d7jn8xh",
                 "secret": "A_armptsqyfpxa4ftvtc739ardncett3uy_cgqx3ku34mh5qdesd7fcaru3gx7tyurr"},
    "nedis": {"brand": "Nedis Smartlife", "client_id": "pettfwyepwpwwhxy57gp",
              "secret": "A_73p8kvkhsted5fxvx8pfudk5hwtmnjr3_yptwxx4t9rkmcppyagwpd43y77tnpw8s"},
    "blitzwolf": {"brand": "Blitzwolf", "client_id": "xpqw7hnghsyvt7y84qr3",
                  "secret": "A_yf3skmg73upyytecsy5tjg58tdmh87t3_vgq3jywdfa8kqyr7eaq7cgm387e53ew9"},
    "tesla": {"brand": "Tesla Smart", "client_id": "gwfwneqcq8xhqghp47wq",
              "secret": "A_3kfxrauppxvtrmknr4mxatacdf7yvmfg_hrwpnqjag5jp3mkcsm59agm8u5dfuxka"},
    "birdlover": {"brand": "BirdLover", "client_id": "gmusrthh3sygeyv3sr38",
                  "secret": "A_x4y4ds9nysv4d3agjyqwmvnptwhgtcwu_pku4cchspfmskfgtaacqcvkfdscx7u7t"},
    "brennenstuhl": {"brand": "Brennenstuhl", "client_id": "dh35afm9ha79sppyxgkf",
                     "secret": "A_aqy9p3e78xr5htpsn95fss5rvcdtaahd_9gyrek4h5ygwshsndqurwjkddtjpw9yr"},
    "proscenic": {"brand": "Proscenic", "client_id": "ja9ntfcxcs8qg5sqdcfm",
                  "secret": "A_4vgq3tcqnam9drtvgam8hneqjprtjnf4_c5rkn5tga889whe5cd7pc9j387knwsuc"},
    "sylvania": {"brand": "Sylvania", "client_id": "creq75hn4vdg5qvrgryp",
                 "secret": "A_ag4xcmp9rjttkj9yf9e8c3wfxry7yr44_wparh3scdv8dc7rrnuegaf9mqmn4snpk"},
    "ultenic": {"brand": "Ultenic", "client_id": "jumhahnc744wvtaj9qgd",
                "secret": "A_jeer4x97qvjhcx7dmxxasst49gya4mn3_dfpfvmmm9sgjfmydrtakcmu38mu3jctv"},
    "woox": {"brand": "Woox Home", "client_id": "pyxevcmw83jg83qca9c7",
             "secret": "A_e3g9q4enqeew9x7xgcqkn8jjcdgwf8py_h8wv7dea7u4hnfc8k8qagr897yuc79ar"},
    "lscsmartconnect": {"brand": "LSC Smart Connect", "client_id": "q594qaqdpy89gmvyndtp",
                        "secret": "A_yegjfwuukevd8qfxw3rjfr5sj43p5gpr_xh59e8qykn4sp7jyh7rwaq3ykfwf8e5n"},
    "alecoair": {"brand": "AlecoAir", "client_id": "pvufcdrftnfkt4rqkxs5",
                 "secret": "A_48vafqcmrfx4mvjrph4j4ayfe9hctnkd_jmehruant8ag7nscxn8u47u9yf8h48e7"},
    "philipssmartselect": {"brand": "Philips Smart Select", "client_id": "ajc33deua7sey8gkg8st",
                          "secret": "A_995k5m8tpah4snp7xu59mcvmfhkhv7mk_kts7cj7mrxgjv7nqcjp9wata3t7ehwya"},
    "noussmart": {"brand": "Nous Smart", "client_id": "dhs3xggvwehvc5tj9xqp",
                  "secret": "A_wwwrnvy7gayy9dvp5nuahyd5d3j4kyxp_7vgwxdy589jtwwee7rugayxrderkekww"},
    "airam": {"brand": "Airam SmartHome", "client_id": "efaxsa7hyadmwvw89mvj",
              "secret": "A_c8cse843mexx8umvdsrqfmx3hs47fk93_jm5tdcyv8hr4kdfq8mxkvf9hj59pte3j"},
    "treatlife": {"brand": "Treatlife", "client_id": "8yncru89qa8495mdutya",
                  "secret": "A_37enmfsnr4r3w8j5cd3fxmhm97gaatxx_y4gn37gryf5ufqhqgh99r9wp3h44dp95"},
    "atomi": {"brand": "Atomi Smart", "client_id": "4upds48whre7hmjdkxdc",
              "secret": "A_k5nk85d8xf3mde4jjjney3s4un7e74a9_ecm3chpyv75nsvuyfk3vp4qd9avjffn7"},
    "kogan": {"brand": "Kogan SmarterHome", "client_id": "e7w4qupjxvym7cyatptt",
              "secret": "A_cs8387f4d574aqh7kkw8rjgtprf3t79y_xfng74ctkrr3q4ehtysh83cmd4xukjya"},
}


class UncoverAuthError(Exception):
    """Invalid email or password."""
    pass


class UncoverError(Exception):
    """API error."""
    pass


def _mobile_hash(data: str) -> str:
    prehash = hashlib.md5(data.encode("utf-8")).hexdigest()
    return prehash[8:16] + prehash[0:8] + prehash[24:32] + prehash[16:24]


def _plain_rsa_encrypt(modulus: int, exponent: int, message: bytes) -> bytes:
    message_int = int.from_bytes(message, "big")
    enc_int = pow(message_int, exponent, modulus)
    return enc_int.to_bytes(256, "big")


def get_devices_with_keys(
    email: str,
    password: str,
    vendor: str = "smartlife",
    region: str = "eu",
    logger=None,
) -> List[Dict[str, Any]]:
    """
    Fetch devices with local_key from Tuya OEM app API.
    Credentials are not stored; used only for this request.

    Args:
        email: Tuya/Smart Life app account email
        password: App password
        vendor: App brand (smartlife, tuya, gosund, nedis, etc.)
        region: eu, us, cn, in
        logger: Optional logger

    Returns:
        List of {id, name, local_key, category, product_id, uuid, mac}
    """
    if vendor not in VENDORS:
        raise UncoverError(f"Unknown vendor: {vendor}. Supported: {', '.join(sorted(VENDORS.keys()))}")

    client_id = VENDORS[vendor]["client_id"]
    secret = VENDORS[vendor]["secret"]
    endpoint = f"https://a1.tuya{region}.com/api.json"

    session = requests.Session()
    sid: Optional[str] = None

    def _sign(data: dict) -> str:
        keys_not_to_sign = ["gid"]
        sorted_keys = sorted(k for k in data.keys() if k not in keys_not_to_sign)
        parts = []
        for k in sorted_keys:
            v = data[k]
            if k == "postData":
                parts.append(f"{k}={_mobile_hash(v)}")
            else:
                parts.append(f"{k}={v}")
        str_to_sign = "||".join(parts)
        return hmac.new(secret.encode("utf-8"), str_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    def _api(action: str, payload: Optional[dict] = None, extra_params: Optional[dict] = None) -> Any:
        nonlocal sid
        params: dict = {
            "a": action,
            "clientId": client_id,
            "v": _API_VERSION,
            "time": str(int(time.time())),
            **(extra_params or {}),
        }
        if sid:
            params["sid"] = sid

        data = {}
        if payload is not None:
            data["postData"] = json.dumps(payload, separators=(",", ":"))

        params["sign"] = _sign({**params, **data})

        resp = session.post(
            endpoint,
            params=params,
            data=data,
            headers={"User-Agent": _USER_AGENT},
        )
        result = resp.json()

        if not result.get("success"):
            err = result.get("errorCode", "")
            msg = result.get("errorMsg", str(result))
            if err == "USER_PASSWD_WRONG":
                raise UncoverAuthError(msg)
            if err == "USER_SESSION_INVALID":
                raise UncoverAuthError(msg)
            raise UncoverError(f"{msg} ({err})")

        return result.get("result")

    # Login
    token_info = _api("tuya.m.user.email.token.create", {"countryCode": "", "email": email})
    passwd_hash = hashlib.md5(password.encode("utf-8")).hexdigest().encode("utf-8")
    enc_pass = _plain_rsa_encrypt(
        int(token_info["publicKey"]),
        int(token_info["exponent"]),
        passwd_hash,
    ).hex()

    login_result = _api(
        "tuya.m.user.email.password.login",
        {
            "countryCode": "",
            "email": email,
            "ifencrypt": 1,
            "options": '{"group": 1}',
            "passwd": enc_pass,
            "token": token_info["token"],
        },
    )
    sid = login_result["sid"]

    # List devices
    devices: List[Dict[str, Any]] = []
    for group in _api("tuya.m.location.list"):
        for dev in _api("tuya.m.my.group.device.list", extra_params={"gid": group["groupId"]}):
            mac = dev.get("mac", "")
            mac_str = ":".join(mac[i:i+2] for i in range(0, min(12, len(mac)), 2)) if mac else ""
            devices.append({
                "id": dev["devId"],
                "name": dev.get("name", dev["devId"]),
                "local_key": dev["localKey"],
                "category": dev.get("category", "unknown"),
                "product_id": dev.get("productId", ""),
                "uuid": dev.get("uuid", ""),
                "mac": mac_str,
            })

    return devices
