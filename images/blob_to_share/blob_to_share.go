package main

import (
	"bytes"
	"context"
	"fmt"
	"log"
	"net/url"
	"os"

	"github.com/Azure/azure-sdk-for-go/sdk/storage/azblob"
	"github.com/Azure/azure-storage-file-go/azfile"
)

// Find an environment variable, or throw an error if it doesn't yet exist
func findEnvVar(name string) string {
	res, found := os.LookupEnv(name)
	if !found {
		log.Fatal(fmt.Sprintf("Environment variable %s not found!", name))
	}
	return res
}

func contains(slice []string, toFind string) bool {
    for _, entry := range slice {
        if entry == toFind {
            return true
        }
    }
    return false
}

func main() {

	// Get the credentials for this account
	accountName, accountKey := findEnvVar("ACCOUNT_NAME"), findEnvVar("ACCOUNT_KEY")
	containerName, shareName := findEnvVar("CONTAINER_NAME"), findEnvVar("SHARE_NAME")

	blobCredential, err := azblob.NewSharedKeyCredential(accountName, accountKey)
	if err != nil {
		log.Fatal("Invalid credentials with error: " + err.Error())
	}
	fileCredential, err := azfile.NewSharedKeyCredential(accountName, accountKey)
	if err != nil {
		log.Fatal(err)
	}

	blobBaseUrl := fmt.Sprintf("https://%s.blob.core.windows.net/", accountName)
	fileBaseUrl := fmt.Sprintf("https://%s.file.core.windows.net/", accountName)

	serviceClient, err := azblob.NewServiceClientWithSharedKey(blobBaseUrl, blobCredential, nil)
	if err != nil {
		log.Fatal("Invalid credentials with error: " + err.Error())
	}

	// List the blobs in the container
	fmt.Println("Listing the blobs in the container:")
	containerClient := serviceClient.NewContainerClient(containerName)
	pager := containerClient.ListBlobsFlat(nil)

	ctx := context.Background()

	// List of all the blobs to upload
	allBlobs := []string{}

	// For each page
	for pager.NextPage(ctx) {
		resp := pager.PageResponse()

		// For each blob on the page
		for _, v := range resp.ContainerListBlobFlatSegmentResult.Segment.BlobItems {
			fmt.Println("  - " + *v.Name)
			allBlobs = append(allBlobs, *v.Name)

			blobClient, err := azblob.NewBlockBlobClientWithSharedKey(blobBaseUrl+containerName+"/"+*v.Name, blobCredential, nil)
			if err != nil {
				log.Fatal(err)
			}

			// Download the blob
			get, err := blobClient.Download(ctx, nil)
			if err != nil {
				log.Fatal(err)
			}

			downloadedData := &bytes.Buffer{}
			reader := get.Body(nil)
			numBytes, err := downloadedData.ReadFrom(reader)
			if err != nil {
				log.Fatal(err)
			}
			err = reader.Close()
			if err != nil {
				log.Fatal(err)
			}

			// Upload to the file share
			u, _ := url.Parse(fmt.Sprintf(fileBaseUrl + shareName + "/" + *v.Name))

			fileURL := azfile.NewFileURL(*u, azfile.NewPipeline(fileCredential, azfile.PipelineOptions{}))

			// Trigger parallel upload with Parallelism set to 3. Note if there is an Azure file
			// with same name exists, UploadBufferToAzureFile will overwrite the existing Azure file with new content,
			// and set specified azfile.FileHTTPHeaders and Metadata.
			err = azfile.UploadBufferToAzureFile(ctx, downloadedData.Bytes(), fileURL,
				azfile.UploadToAzureFileOptions{
					Parallelism: 3,
					FileHTTPHeaders: azfile.FileHTTPHeaders{
						CacheControl: "no-transform",
					},
					Metadata: azfile.Metadata{},
					// If Progress is non-nil, this function is called periodically as bytes are uploaded.
					Progress: func(bytesTransferred int64) {
						fmt.Printf("    Uploaded %d of %d bytes.\n", bytesTransferred, numBytes)
					},
				})
			if err != nil {
				log.Fatal(err)
			}

		}

	}

	// Remove any files in the share that are not in the blob container
	shareUrl, _ := url.Parse(fmt.Sprintf(fileBaseUrl + shareName))
	directoryURL := azfile.NewDirectoryURL(*shareUrl, azfile.NewPipeline(fileCredential, azfile.PipelineOptions{}))
	
	// List the file(s) and directory(s) in our share's root directory; since a directory may hold millions of files and directories, this is done 1 segment at a time.
	for marker := (azfile.Marker{}); marker.NotDone(); { // The parentheses around azfile.Marker{} are required to avoid compiler error.
		// Get a result segment starting with the file indicated by the current Marker.
		listResponse, err := directoryURL.ListFilesAndDirectoriesSegment(ctx, marker, azfile.ListFilesAndDirectoriesOptions{})
		if err != nil {
			log.Fatal(err)
		}
		// IMPORTANT: ListFilesAndDirectoriesSegment returns the start of the next segment; you MUST use this to get
		// the next segment (after processing the current result segment).
		marker = listResponse.NextMarker

		// Process the files returned in this result segment (if the segment is empty, the loop body won't execute)
		for _, fileEntry := range listResponse.FileItems {

			if !contains(allBlobs, fileEntry.Name) {
				fmt.Println("File in share and not blob container to be deleted: " + fileEntry.Name)

				fileURL := directoryURL.NewFileURL(fileEntry.Name)

				// Delete the file not in the blob
				_, err = fileURL.Delete(ctx)
				if err != nil {
					log.Fatal(err)
				}

			}

		}

	}

}
