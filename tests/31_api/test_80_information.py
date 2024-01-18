from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile


def test_get_blind_info(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    blinds_type_dict = {
        "sng": ["standard", "turbo"],
        "mtt": ["standard", "turbo", "hyper_turbo"]
    }

    for blind in blinds_type_dict:
        blinds_type = blind
        for b_s_l in blinds_type_dict[blind]:
            blinds_structure = b_s_l
            response = api_client.get(f"/v1/info/{blinds_type}/{blinds_structure}/blinds_info")
            assert response.status_code == 200
            assert isinstance(response.json(), list)


# def test_get_payment_structure(api_client: TestClient, api_guest: UserAccessProfile):
#     # set headers
#     api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

#     payment_structure_list = [
#         {"players": "1-3", "position": {"first": "100%", "second": "0", "third": "0"}},
#         {"players": "4-6", "position": {"first": "70%", "second": "30%", "third": "0"}},
#         {"players": "7-9", "position": {"first": "50%", "second": "30%", "third": "20%"}}
#     ]

#     response = api_client.get(f"/v1/info/payment structure")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert response.json() == payment_structure_list
