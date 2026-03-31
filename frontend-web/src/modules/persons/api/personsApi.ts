import { http } from '@/shared/api/http'
import type {
  ApiEnvelope,
  PersonCreatePayload,
  PersonDetailReadModel,
  PersonListReadModel,
  PersonQueryParams,
  PersonReadModel,
  PersonUpdatePayload
} from '@/shared/model/types'

export async function fetchPersons(params?: PersonQueryParams) {
  return (await http.get<ApiEnvelope<PersonListReadModel>>('/app/persons', { params })).data.data
}

export async function createPerson(payload: PersonCreatePayload) {
  return (await http.post<ApiEnvelope<PersonReadModel>>('/app/persons', payload)).data.data
}

export async function fetchPerson(personId: string) {
  return (await http.get<ApiEnvelope<PersonDetailReadModel>>(`/app/persons/${personId}`)).data.data
}

export async function updatePerson(personId: string, payload: PersonUpdatePayload) {
  return (await http.patch<ApiEnvelope<PersonReadModel>>(`/app/persons/${personId}`, payload)).data.data
}

export async function deletePerson(personId: string) {
  await http.delete(`/app/persons/${personId}`)
}
