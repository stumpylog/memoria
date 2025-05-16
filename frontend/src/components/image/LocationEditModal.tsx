// src/components/image/LocationEditModal.tsx

import type { AxiosError as AxiosErrorType, AxiosResponse } from "axios"; // Import Axios types

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

// Updated ApiError to better reflect AxiosError structure if needed,
// or use AxiosErrorType directly in useQuery/useMutation.
// For simplicity, we'll use AxiosErrorType for TError.
export interface ApiError
  extends AxiosErrorType<{
    message?: string;
    detail?: string | Array<{ msg: string; type: string }>;
  }> {}

import type {
  CountryListItemSchemaOut,
  ImageLocationSchemaOut,
  ImageLocationUpdateSchemaIn,
  SubdivisionListItemSchemaOut,
} from "../../api"; // Adjust path as needed

// API functions are assumed to return Promise<AxiosResponse<YourType>>
import {
  imageUpdateLocation,
  locationGetCities,
  locationGetCountries,
  locationGetSubdivisions,
  locationGetSubLocations,
} from "../../api"; // Adjust path as needed

interface LocationEditModalProps {
  show: boolean;
  onHide: () => void;
  imageId: number;
  currentLocation: ImageLocationSchemaOut | null;
}

const LocationEditModal: React.FC<LocationEditModalProps> = ({
  show,
  onHide,
  imageId,
  currentLocation,
}) => {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting: isFormSubmitting },
    reset,
  } = useForm<ImageLocationUpdateSchemaIn>({
    defaultValues: {
      city: currentLocation?.city || null,
      country_code: currentLocation?.country_code || "",
      sub_location: currentLocation?.sub_location || null,
      subdivision_code: currentLocation?.subdivision_code || null,
    },
  });

  const selectedCountry = watch("country_code");
  const selectedSubdivision = watch("subdivision_code");
  const selectedCity = watch("city");

  // Fetch countries
  const {
    data: countries = [], // Default to empty array, data is now CountryListItemSchemaOut[]
    isLoading: isLoadingCountries,
    isError: isErrorCountries,
    error: errorCountries,
  } = useQuery<
    CountryListItemSchemaOut[], // TQueryFnData / TData: The actual data type
    ApiError // TError
  >({
    queryKey: ["countries"],
    queryFn: async (): Promise<CountryListItemSchemaOut[]> => {
      const response: AxiosResponse<CountryListItemSchemaOut[]> = await locationGetCountries({
        throwOnError: true,
      });
      return response.data; // Extract data from AxiosResponse
    },
    staleTime: 5 * 60 * 1000,
  });

  // Fetch subdivisions
  const {
    data: subdivisions = [],
    isLoading: isLoadingSubdivisions,
    isError: isErrorSubdivisions,
    error: errorSubdivisions,
  } = useQuery<SubdivisionListItemSchemaOut[], ApiError>({
    queryKey: ["subdivisions", selectedCountry],
    queryFn: async (): Promise<SubdivisionListItemSchemaOut[]> => {
      const response: AxiosResponse<SubdivisionListItemSchemaOut[]> =
        await locationGetSubdivisions({
          query: { country_code: selectedCountry },
          throwOnError: true,
        });
      return response.data;
    },
    enabled: !!selectedCountry,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch cities
  const {
    data: cities = [],
    isLoading: isLoadingCities,
    isError: isErrorCities,
    error: errorCities,
  } = useQuery<string[], ApiError>({
    queryKey: ["cities", selectedCountry, selectedSubdivision],
    queryFn: async (): Promise<string[]> => {
      const response: AxiosResponse<string[]> = await locationGetCities({
        query: { country_code: selectedCountry, subdivision_code: selectedSubdivision || "" },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!selectedCountry && !!selectedSubdivision,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch sub-locations
  const {
    data: subLocations = [],
    isLoading: isLoadingSubLocations,
    isError: isErrorSubLocations,
    error: errorSubLocations,
  } = useQuery<string[], ApiError>({
    queryKey: ["subLocations", selectedCountry, selectedSubdivision, selectedCity],
    queryFn: async (): Promise<string[]> => {
      const response: AxiosResponse<string[]> = await locationGetSubLocations({
        query: {
          country_code: selectedCountry,
          subdivision_code: selectedSubdivision || "",
          city_name: selectedCity || "",
        },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!selectedCountry && !!selectedSubdivision && !!selectedCity,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (show) {
      reset({
        city: currentLocation?.city || null,
        country_code: currentLocation?.country_code || "",
        sub_location: currentLocation?.sub_location || null,
        subdivision_code: currentLocation?.subdivision_code || null,
      });
      setSubmitError(null);
    }
  }, [reset, show, currentLocation]);

  useEffect(() => {
    if (selectedCountry === "" || selectedCountry === null) {
      setValue("subdivision_code", null);
      setValue("city", null);
      setValue("sub_location", null);
    }
  }, [selectedCountry, setValue]);

  useEffect(() => {
    if (selectedSubdivision === "" || selectedSubdivision === null) {
      setValue("city", null);
      setValue("sub_location", null);
    }
  }, [selectedSubdivision, setValue]);

  useEffect(() => {
    if (selectedCity === "" || selectedCity === null) {
      setValue("sub_location", null);
    }
  }, [selectedCity, setValue]);

  const updateLocationMutation = useMutation<
    ImageLocationSchemaOut, // TData: Actual data type from response.data
    ApiError, // TError
    ImageLocationUpdateSchemaIn // TVariables
  >({
    mutationFn: async (data: ImageLocationUpdateSchemaIn): Promise<ImageLocationSchemaOut> => {
      const response: AxiosResponse<ImageLocationSchemaOut> = await imageUpdateLocation({
        path: { image_id: imageId },
        body: data,
      });
      return response.data; // Extract data from AxiosResponse
    },
    onSuccess: (updatedLocationData) => {
      // updatedLocationData is ImageLocationSchemaOut
      queryClient.invalidateQueries({ queryKey: ["image", imageId, "location"] });
      // Optionally, update the cache directly with the new data
      queryClient.setQueryData(["image", imageId, "location"], updatedLocationData);
      queryClient.invalidateQueries({ queryKey: ["images"] });
      onHide();
    },
    onError: (err) => {
      console.error("Failed to update location:", err);
      const message = err.response?.data?.detail
        ? typeof err.response.data.detail === "string"
          ? err.response.data.detail
          : err.response.data.detail.map((d) => d.msg).join(", ")
        : err.response?.data?.message ||
          err.message ||
          "An unexpected error occurred. Please try again.";
      setSubmitError(message);
    },
  });

  const onSubmit = (data: ImageLocationUpdateSchemaIn) => {
    setSubmitError(null);
    const sanitizedData: ImageLocationUpdateSchemaIn = {
      ...data,
      country_code: data.country_code === "" ? "" : data.country_code,
      city: data.city === "" ? null : data.city,
      sub_location: data.sub_location === "" ? null : data.sub_location,
      subdivision_code: data.subdivision_code === "" ? null : data.subdivision_code,
    };
    updateLocationMutation.mutate(sanitizedData);
  };

  const getErrorMessage = (error: ApiError | null): string => {
    if (!error) return "An unknown error occurred.";
    if (error.response?.data?.detail) {
      if (typeof error.response.data.detail === "string") {
        return error.response.data.detail;
      }
      return error.response.data.detail.map((d) => d.msg).join(", ");
    }
    return (
      error.response?.data?.message || error.message || "An error occurred while fetching data."
    );
  };

  if (isLoadingCountries && show) {
    return (
      <Modal show={show} onHide={onHide} centered backdrop="static">
        <Modal.Header closeButton={!updateLocationMutation.isPending && !isFormSubmitting}>
          <Modal.Title>Edit Location Information</Modal.Title>
        </Modal.Header>
        <Modal.Body className="text-center p-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading essential data...</span>
          </Spinner>
          <p className="mt-3">Loading location options...</p>
        </Modal.Body>
      </Modal>
    );
  }

  return (
    <Modal show={show} onHide={onHide} centered backdrop="static">
      <Modal.Header closeButton={!updateLocationMutation.isPending && !isFormSubmitting}>
        <Modal.Title>Edit Location Information</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {submitError && <Alert variant="danger">{submitError}</Alert>}
          {updateLocationMutation.isError && !submitError && (
            <Alert variant="danger">
              Failed to update location information.{" "}
              {getErrorMessage(updateLocationMutation.error)}
            </Alert>
          )}

          {currentLocation && (
            <div className="mb-3">
              <h6>Current Location:</h6>
              <p className="text-muted small">
                {[
                  currentLocation.sub_location,
                  currentLocation.city,
                  currentLocation.subdivision_name,
                  currentLocation.country_name,
                ]
                  .filter(Boolean)
                  .join(", ") || "No location data set"}
              </p>
            </div>
          )}

          {isErrorCountries && (
            <Alert variant="warning" className="mb-3">
              Could not load countries: {getErrorMessage(errorCountries)}. Some functionality may
              be limited.
            </Alert>
          )}

          <Form.Group className="mb-3">
            <Form.Label>Country</Form.Label>
            <Form.Select
              {...register("country_code", { required: "Country is required" })}
              isInvalid={!!errors.country_code}
              disabled={isLoadingCountries || isErrorCountries || updateLocationMutation.isPending}
            >
              <option value="">Select a country...</option>
              {/* `countries` is now directly CountryListItemSchemaOut[] */}
              {countries.map((country) => (
                <option key={country.alpha2} value={country.alpha2}>
                  {country.best_name}
                </option>
              ))}
            </Form.Select>
            {errors.country_code && (
              <Form.Control.Feedback type="invalid">
                {errors.country_code.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          {selectedCountry && (
            <Form.Group className="mb-3">
              <Form.Label>
                State/Province
                {isLoadingSubdivisions && (
                  <Spinner animation="border" size="sm" className="ms-2" />
                )}
              </Form.Label>
              {isErrorSubdivisions && (
                <Alert variant="warning" className="p-2 small">
                  Could not load states/provinces: {getErrorMessage(errorSubdivisions)}
                </Alert>
              )}
              <Form.Select
                {...register("subdivision_code")}
                disabled={
                  isLoadingSubdivisions ||
                  !selectedCountry ||
                  isErrorSubdivisions ||
                  updateLocationMutation.isPending
                }
              >
                <option value="">Select a state/province (optional)...</option>
                {/* `subdivisions` is now directly SubdivisionListItemSchemaOut[] */}
                {subdivisions.map((subdivision) => (
                  <option key={subdivision.code} value={subdivision.code}>
                    {subdivision.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          )}

          {selectedCountry && selectedSubdivision && (
            <Form.Group className="mb-3">
              <Form.Label>
                City
                {isLoadingCities && <Spinner animation="border" size="sm" className="ms-2" />}
              </Form.Label>
              {isErrorCities && (
                <Alert variant="warning" className="p-2 small">
                  Could not load cities: {getErrorMessage(errorCities)}
                </Alert>
              )}
              <Controller
                name="city"
                control={control}
                render={({ field }) => (
                  <Form.Control
                    {...field}
                    as="input"
                    list="city-options"
                    placeholder="Select or enter city (optional)..."
                    value={field.value || ""}
                    onChange={(e) => field.onChange(e.target.value || null)}
                    disabled={
                      !selectedSubdivision ||
                      isLoadingCities ||
                      isErrorCities ||
                      updateLocationMutation.isPending
                    }
                  />
                )}
              />
              <datalist id="city-options">
                {/* `cities` is now directly string[] */}
                {cities.map((city: string) => (
                  <option key={city} value={city} />
                ))}
              </datalist>
              <Form.Text className="text-muted">
                Dependent on state/province. Select or type a new one.
              </Form.Text>
            </Form.Group>
          )}

          {selectedCountry && selectedSubdivision && selectedCity && (
            <Form.Group className="mb-3">
              <Form.Label>
                Specific Location
                {isLoadingSubLocations && (
                  <Spinner animation="border" size="sm" className="ms-2" />
                )}
              </Form.Label>
              {isErrorSubLocations && (
                <Alert variant="warning" className="p-2 small">
                  Could not load specific locations: {getErrorMessage(errorSubLocations)}
                </Alert>
              )}
              <Controller
                name="sub_location"
                control={control}
                render={({ field }) => (
                  <Form.Control
                    {...field}
                    as="input"
                    list="sublocation-options"
                    placeholder="e.g. Eiffel Tower (optional)..."
                    value={field.value || ""}
                    onChange={(e) => field.onChange(e.target.value || null)}
                    disabled={
                      !selectedCity ||
                      isLoadingSubLocations ||
                      isErrorSubLocations ||
                      updateLocationMutation.isPending
                    }
                  />
                )}
              />
              <datalist id="sublocation-options">
                {/* `subLocations` is now directly string[] */}
                {subLocations.map((location: string) => (
                  <option key={location} value={location} />
                ))}
              </datalist>
              <Form.Text className="text-muted">
                Dependent on city. Select or type a new one.
              </Form.Text>
            </Form.Group>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={onHide}
            disabled={updateLocationMutation.isPending || isFormSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isFormSubmitting || updateLocationMutation.isPending || isLoadingCountries}
          >
            {isFormSubmitting || updateLocationMutation.isPending ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Saving...
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default LocationEditModal;
