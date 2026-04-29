from .analytics import AnalyticsChannelClient
import asyncio

analytics_dlt_client = AnalyticsChannelClient("http://localhost:9337")

adc = analytics_dlt_client  # easier to understand :)

id: str = asyncio.run(adc.record_data_fetch("run-1234", "some-model", "93120", {"a": 2, "b": ['z']}, {"a": 2, "b": ['z']}, time_range_start="1234", time_range_end="2345"))

print(asyncio.run(adc.get_record(id)))
