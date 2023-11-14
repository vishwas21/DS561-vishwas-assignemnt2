import apache_beam as beam

from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions

class ProcessHTMLFiles(beam.DoFn):
  def process(self, element):
    file_name, content = element
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    listOfAnchorTags = soup.find_all('a')

    link_list = []

    for anchorTag in listOfAnchorTags:
        hrefLink = anchorTag.get('href')
        link_list.append((file_name, hrefLink))
    
    return link_list

    
def run():

  pipeline_options = PipelineOptions(runner='DataflowRunner')
  google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)

  google_cloud_options.project = 'ds561-visb-assignment' 
  google_cloud_options.staging_location = 'gs://cs561-assignment2-storage-bucket'
  google_cloud_options.temp_location = 'gs://dataflow-apache-ds561-visb-assignment'
  google_cloud_options.region = 'us-east4'  

  file_list = ["{}.html".format(i) for i in range(0, 10000)]

  with beam.Pipeline(options=pipeline_options) as p:
    data = (p | 'ReadFromGCSWithFilename' >> beam.io.ReadFromTextWithFilename(f'gs://cs561-assignment2-storage-bucket/files/*.html') \
            | 'ProcessDataAndGetLinks' >> beam.ParDo(ProcessHTMLFiles()))
    
    outgoingCount = (data | 'outgoingCount' >> beam.combiners.Count.PerKey() \
                        | 'topFiveOutgoing' >> beam.transforms.combiners.Top.Of(5, key=lambda x: x[1]) \
                        | 'writeToStorageBucketOutgoing' >> beam.io.WriteToText('gs://dataflow-apache-ds561-visb-assignment/outgoing'))
    
    incomingCount = (data | 'incomingTransform' >> beam.Map(lambda swapTuple: (swapTuple[1], swapTuple[0]))
                        | 'incomingCount' >> beam.combiners.Count.PerKey() \
                        | 'topFiveIncoming' >> beam.transforms.combiners.Top.Of(5, key=lambda x: x[1]) \
                        | 'writeToStorageBucketIncoming' >> beam.io.WriteToText('gs://dataflow-apache-ds561-visb-assignment/incoming'))


if __name__ == '__main__':
  run()